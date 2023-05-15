#include "DFParser.h"
#include <iostream>
#include "json.hpp"
#include <fcntl.h>
#include <sys/mman.h>
#include <iomanip>
#include <sstream>
#include <boost/algorithm/string/join.hpp> // Include for boost::split

using namespace std;
using namespace nlohmann;

int main(int argc, char** argv) {
    if (argc < 2) {
        cout << "too few arguments" << endl;
        return 1;
    }

    std::ios::sync_with_stdio(false);

    int fp = open(argv[1], O_RDONLY, 0);
    size_t logdata_len = lseek(fp, 0, SEEK_END);
    lseek(fp, 0, SEEK_SET);
    uint8_t* logdata = (uint8_t*)mmap(0, logdata_len, PROT_READ, MAP_SHARED, fp, 0);
    madvise(logdata, logdata_len, POSIX_MADV_SEQUENTIAL);

    DFParser parser(logdata, logdata_len);

    uint64_t count=0;
    uint8_t type;
    DFParser::message_t msg;

    json stats;

    stats["totalcount"] = 0;
    stats["totalbytes"] = 0;
    stats["msgs"] = json::object();

    while(parser.next_message(msg)) {
        auto name = parser.get_message_name(msg);

        if (!stats["msgs"].contains(name)) {
            stats["msgs"][name]["count"] = 0;
            stats["msgs"][name]["bytes"] = 0;
        }

        stats["msgs"][name]["count"] = (double)stats["msgs"][name]["count"] + 1;
        stats["msgs"][name]["bytes"] = (double)stats["msgs"][name]["bytes"] + parser.get_message_size_including_header(msg);

        stats["totalcount"] = (double)stats["totalcount"] + 1;
        stats["totalbytes"] = (double)stats["totalbytes"] + parser.get_message_size_including_header(msg);
    }

    for (auto& [key,value] : stats["msgs"].items()) {
        cout << key << "," << (int)value["bytes"] << endl;
    }
    return 0;
}
