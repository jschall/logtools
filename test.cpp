#include "DFParser.h"
#include <fstream>
#include <boost/iostreams/device/mapped_file.hpp>
#include <iostream>

using namespace std;

int main(int argc, char** argv) {
    if (argc < 2) {
        cout << "too few arguments" << endl;
        return 1;
    }
    ifstream f(argv[1], ifstream::binary);
    char buf[1024*16];
    f.rdbuf()->pubsetbuf(buf, sizeof(buf));

    auto parser = DFLogParser(f);

    uint64_t count=0;
    uint8_t type;
    vector<uint8_t> msgbody;
    while(parser.next_msg_body(type, msgbody)) {
//         cout << (int)type << endl;
        count++;

//         parser.print_msg(msg);
//         cout << msg["__format__"]["name"] << endl;
//         cout << msg << endl;
    }
    cout << count << endl;

    return 0;
}
