

static const char* const HELP = "FrameCatcher: Attempts to report what frames were used by this stream in the last cook.\nOutput files will report the input sourcefile and the OutputContext requested (generally this will be the input's frame number, unless you've got expressions there..";
static const char* const CLASS = "FrameCatcher";
static const char* const VERSION = "0.91-debug";
/*
0.91 - additional inclusion of a convieneince field/header to help with the compacting process
0.9d - minor tweak to the guard positioning in _open, trying to minimise the time we could be
       having clashes
0.9c - added in two FuryFX convieniences - the file and frame fragments.
0.9b - help text refined, and the default outfile set to be more sane (so it Just Works)
0.9a - first trial release


*/

static const char* const AUTHOR = "anthony.tan@rhubarbfizz.com";

static const char* const NODE_HELP = "This is an attempt at what is basically a wiretap node. Usage is\n\
to insert it straight after the Read node you want to monitor\n\
python) and use a before-frame script to increment the file it's\n\
writing to (or alternatively, pad in a header/divider).\n\n\
You could use it interactively but it leans heavily on Nuke's\n\
image request architecture so it's going to depend on what nuke\n\
requests from the read node - which *will* weird out with caching\n\
and nuke optimising requests.\n\n\
(Note: Technically if you leave the node in and monitoring, there is\n\
a memory leak condition - the std::string isn't flushed til a write.\n\n\
* clock_rst (toggle to empty buffer):\n\
every time you toggle this, the internal buffer is cleared and a\n\
counter incremented to modify the node's hash to trigger\n\
recomputation (like clocking a flop). This will probably\n\n\
* monitor_enable:\n\
if enabled, the node is actively tapping the tree. If not, write\n\
behaviour will still occur.\n\n\
* write_enable:\n\
if enabled, each time an _open() call is made it writes out\n\
and clears the internal buffer. If not relying on frame-specific logs\n\
you could optimise the file I/O by only enabling this periodically.";


static const char* FIELD_SEPARATOR = "\t";
static const char* DIVIDER = "\n";
static const char* DEFAULT_OUTFILE  = "[value root_fragment].[value name].[value frame_fragment].txt";
static const char* DEFAULT_ROOT_FRAGMENT  = "[file dirname [value root.name]]/[value name]";
static const char* DEFAULT_COL_HEADER_FRAGMENT = "[python nuke.thisNode().input(0).name()]";
static const char* DEFAULT_FRAME_FRAGMENT  = "0000001";


#include <DDImage/NukeWrapper.h>
#include <DDImage/Iop.h>
#include <DDImage/Row.h>
#include <DDImage/Knobs.h>
#include <DDImage/Thread.h>
#include <DDImage/Reader.h>
#include <DDImage/MetaData.h>

#ifdef __insane__
    // note there isnt any good reason for the shared mem now
    // really? Ugh. Windows specific now for FrameCatcher
    #include <Windows.h>
    // for StringCbPrintf
    #include <Strsafe.h> 
#endif


#include <iostream>
#include <fstream>

using namespace DD::Image;
using namespace std;

class FrameCatcher : public Iop {
    private:
        const char* _dumpfile;
        const char* _nodehelp;
		const char* _rootfragment;
		const char* _framefragment;
		const char* _colheaderfragment;
        std::string _localbuffer;
        bool _clock;
		bool _clock2;
        bool _write_out;
		bool _cout_override;
        bool _monitor;
        Lock _lock;
        int _hash_modding_counter;

    
    public:
        // one pipe in, one pipe out
        int maximum_inputs() const {return 1;}
        int minimum_inputs() const {return 1;}

        // constructor
        FrameCatcher (Node* node) : Iop (node)
        {
            
            _localbuffer.clear();
			_cout_override = false;
            _write_out = false;    // do not write out by default
            _monitor = false;    // do not monitor by default
            _clock = false;
			_clock2 = false;
            _hash_modding_counter = 0;
            _dumpfile = DEFAULT_OUTFILE;
            _nodehelp = NODE_HELP;
			_rootfragment = DEFAULT_ROOT_FRAGMENT;
			_framefragment = DEFAULT_FRAME_FRAGMENT;
			_colheaderfragment = DEFAULT_COL_HEADER_FRAGMENT;

            // clock bit is a way to flush the buffer ONLY
            // validate is the only spot where you will write a file
            // and then only if you have the write flag flipped 
            // cout << CLASS <<  "::constructed with hash:" << DD::Image::Iop::hash() << endl;
        }

        // destructor
        ~FrameCatcher() {
            // nothing here. _firstTime is stack memory only
            cout << CLASS <<  "::destructor called" << endl;
        }

        void _validate(bool for_real);
        void _request(int x, int y, int r, int t, ChannelMask channels, int count);
        void _open(void);
        void _close(void);

        void engine (int y, int x, int r, ChannelMask channels, Row& out);

        // implement append so we can use our hash modification counter - on clock we always flag
        // the tree as being dirty. It's a bit inefficient, i know..
        void append(Hash& hash);
         
        // this should intercept knobs being changed, so we can just not do stuff..
        int knob_changed(Knob* k);

        void knobs(Knob_Callback f){

            // derr. Should be a file knob. Although, this makes interesting oddnesses
            // since it should always use global frame, not perturbed frame, which is
            // what it will be getting. No other nuke node does odd time inspection like this
            // basically. Don't expect sane results using a .####/%04d frame calculation here.
            //
            // If you want to make this frame-sane, then shoot me a feature request since it'll 
            // require custom building.
            File_knob(f, &_dumpfile, "out_file", "Output File");
            SetFlags(f, DD::Image::Knob::NO_RERENDER );
            Newline(f);
            Bool_knob(f, &_clock, "clock_rst", "Toggle to empty buffer");
            // this is considered a dirty flag. this being changed will force recalc which
            // is ideal for us, as we want to force upstream request. 
            Newline(f);
            Bool_knob(f, &_clock, "clock", "Non-buffer emptying clock");
            // this is considered a dirty flag. this being changed will force recalc which
            // is ideal for us, as we want to force upstream request. 
            Newline(f);
            Bool_knob(f, &_monitor, "monitor_enable", "Enable monitoring of requests");
            SetFlags(f, DD::Image::Knob::NO_RERENDER );
            
            Newline(f);
            Bool_knob(f, &_write_out, "write_enable", "Enable write out of data to the dump file on each frame _open call");
            SetFlags(f, DD::Image::Knob::NO_RERENDER );

			VSpacer(f, 15);
			Divider(f, "FuryFX convienience helpers");
			String_knob(f, &_rootfragment, "root_fragment", "Root Fragment");
			SetFlags(f, DD::Image::Knob::NO_RERENDER );
			Newline(f);

			Bool_knob(f, &_cout_override, "cout_override", "DEBUG: force dump only to stderr");
            SetFlags(f, DD::Image::Knob::NO_RERENDER );

			Newline(f);
			String_knob(f, &_framefragment, "frame_fragment", "Frame Fragment");
            SetFlags(f, DD::Image::Knob::NO_RERENDER );

			Newline(f);
			String_knob(f, &_colheaderfragment, "column_header", "Column Header");
            SetFlags(f, DD::Image::Knob::NO_RERENDER );
			
			Newline(f);
			
			//Divider(f);
			//Button(f, "dump_buffer", "buffer -> stdout");
			//SetFlags(f, DD::Image::Knob::NO_RERENDER );

            Divider(f);
            BeginClosedGroup(f, "readme");
            Text_knob(f, _nodehelp);
            SetFlags(f, DD::Image::Knob::NO_RERENDER);
            EndGroup(f);

			Divider(f);
			Named_Text_knob(f,"class", CLASS);
			Spacer(f, 12);
			Text_knob(f, "v");
			Named_Text_knob(f,"version", VERSION);
            }

        const char* Class() const { return CLASS; }
        const char* node_help() const { return HELP; }

        // this syntax looks odd, but half familliar as an init 
        static const Iop::Description description;
    };  




// you must have this as your entry point i suspect..
static Iop* FrameCatcherCreate(Node* node){
    return new FrameCatcher(node);
    }

// weird, i can't get Nuke 7 style iop description loaders.. 
const Iop::Description FrameCatcher::description(CLASS, "ignore_this", FrameCatcherCreate);

void FrameCatcher::_close(void){
    // cout << CLASS <<  "::_close called" << endl;
    }

int FrameCatcher::knob_changed(Knob* k){
    if (k->is("clock_rst")){
        _localbuffer.clear();
        _hash_modding_counter+=1;
        // cout << _hash_modding_counter << endl;
        cout << CLASS <<  "::clock rst, new hash:" << DD::Image::Iop::hash() << endl;
        }
	else if(k->is("clock")){
        _hash_modding_counter+=1;
        cout << CLASS <<  "::clock, new hash:" << DD::Image::Iop::hash() << endl;
        }

    return true;
    }

void FrameCatcher::append(Hash& hash) {
         hash.append(_hash_modding_counter);
         }


void FrameCatcher::_validate(bool for_real){

    // take all inputs from input0, and validate. should be
    // done up as a passthrough
    copy_info();
    
    // MetaData::Bundle metadata_bundle;
    // metadata_bundle = DD::Image::Op::fetchMetaData(NULL); // get the whole bundle

    //cout << CLASS << "::_validate called" << endl;
    //cout << CLASS << metadata_bundle.getString(DD::Image::MetaData::FILENAME) << endl;

    // Interestingly enough, _validate() is called first on the target frame BEFORE
    // time perturbs are triggered from oflow. This results in a mis-reporting.
    // e.g. : render out frame 53 which needs source 10,11 and you'll get a report 
    //        here for source 53 as well as 10, 11. Odd. This is one of the reasons
    //        that the engine call is pushed into _open
    }


void FrameCatcher::_request(int x, int y, int r, int t, ChannelMask channels, int count){
    // we want to make sure we don't affect the stream, so request all channels
    ChannelSet readChannels = input0().info().channels();

    // however, we *are* going to just request 1:1
    input(0)->request( x, y, r, t, readChannels, count );    
    }


void FrameCatcher::_open(void){
    MetaData::Bundle metadata_bundle;
    OutputContext oc;
    std::ofstream frame_dump_file;
    std::ostringstream ss;
	
	
    {
		Guard guard(_lock);
        if (_monitor) {
		    metadata_bundle = DD::Image::Op::fetchMetaData(NULL); // get the whole bundle
	        oc = DD::Image::Iop::outputContext();
            // cout << CLASS << "::_open called" << endl;
            // cout << CLASS << metadata_bundle.getString(DD::Image::MetaData::FILENAME) << endl;

            // should wrap this into a stream properly.
            // the old reason for _localbuffer was for console reporting 
            // (it's persistent - the stream is not because i'm tired of stream history 
            // breaking my code)
			_localbuffer += _colheaderfragment;
			_localbuffer += FIELD_SEPARATOR;
            _localbuffer += metadata_bundle.getString(DD::Image::MetaData::FILENAME);
            _localbuffer += FIELD_SEPARATOR;
            ss << oc.frame();
            _localbuffer += ss.str();
            _localbuffer += DIVIDER;
            }
		
		
		// we don't actually need to guard the monitor, only the writer
		
        if (_write_out) {
			if(_cout_override) {
				cout << CLASS << "::write::" << _localbuffer << endl;
				}
			else {
				frame_dump_file.open(_dumpfile, ios::out | ios::app); // append
				frame_dump_file << _localbuffer;
				frame_dump_file.flush();
				frame_dump_file.close();
				}
			_localbuffer.clear();
            }
        }// guard zone
    }

void FrameCatcher::engine(int y, int x, int r, ChannelMask channels, Row& row){
    // define the row
    Row in(x,r);
    
    // fetch from input 0 what was requested in the engine
    in.get(input0(), y, x, r, channels);
    if (aborted()){
        return;
        }

    foreach (z, channels) {
        float* CUR = row.writable(z) + x;    // current initted to be the row structure (initted to be the right size)
                                            // and had the ptr set to be the right z (channel) point
        const float* inptr = in[z] + x;     // input is the same, just diff notation
        const float* END = row[z] + r;      // end is row's [z] chan, + r offset. x = start off, y = end off
        while (CUR < END) {
            *CUR++ = *inptr++;    // whatever is at CUR = whatever is at inptr. then increment pointers and do it again
            }
        }
    }    