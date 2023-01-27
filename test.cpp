#include "DFParser.h"
#include <fstream>
#include <boost/iostreams/device/mapped_file.hpp>
#include <iostream>
#include "json.hpp"

using namespace std;
using namespace nlohmann;

int main(int argc, char** argv) {
    if (argc < 3) {
        cout << "too few arguments" << endl;
        return 1;
    }
    ifstream f(argv[1], ifstream::binary);
    char buf[1024*16];
    f.rdbuf()->pubsetbuf(buf, sizeof(buf));

    DFLogParser parser(f);


    json TimeUS = json::array();
    json Volt = json::array();
    json VoltR = json::array();
    json Curr = json::array();
    json CurrTot = json::array();
    json Res = json::array();

    uint64_t count=0;
    uint8_t type;
    DFLogParser::message_t msg;
    while(parser.next_message(msg)) {
        int instance;
        if (parser.get_message_name(msg) == "BAT" && parser.get_scalar_field(msg, "Instance", instance) && instance == 0) {
            uint64_t t;
            if (parser.get_scalar_field(msg, "TimeUS", t)) {
                TimeUS.push_back(t);
            }

            float val;
            if (parser.get_scalar_field(msg, "VoltR", val)) {
                VoltR.push_back(val);
            }

            if (parser.get_scalar_field(msg, "Volt", val)) {
                Volt.push_back(val);
            }
            if (parser.get_scalar_field(msg, "Curr", val)) {
                Curr.push_back(val);
            }
            if (parser.get_scalar_field(msg, "CurrTot", val)) {
                CurrTot.push_back(val);
            }
            if (parser.get_scalar_field(msg, "Res", val)) {
                Res.push_back(val);
            }
        }
//         cout << (int)msg.type << endl;
        count++;
    }
    cout << count << endl;

    json j;
    j["BAT[0]"]["TimeUS"]  = TimeUS;
    j["BAT[0]"]["VoltR"]   = Volt;
    j["BAT[0]"]["Volt"]    = VoltR;
    j["BAT[0]"]["Curr"]    = Curr;
    j["BAT[0]"]["CurrTot"] = CurrTot;
    j["BAT[0]"]["Res"]     = Res;

    ofstream outfile(argv[2]);
    outfile << json::to_msgpack(j) << endl;

    return 0;
}
