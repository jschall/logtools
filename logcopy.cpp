#include "DFParser.h"
#include <iostream>
#include "json.hpp"
#include <fcntl.h>
#include <sys/mman.h>
#include <iomanip>
#include <sstream>
#include <boost/algorithm/string/join.hpp> // Include for boost::split
#include <fstream>

using namespace std;
using namespace nlohmann;

int main(int argc, char** argv) {
    if (argc < 3) {
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


    auto outfile = fopen(argv[2], "wb");

    json stats;

//     int sonr_cnt = 0;
//     int ntun_cnt = 0;
//     int tpff_cnt = 0;
//     int bat_cnt[16] = {};
//     int ahr2_cnt = 0;
//     int pidr_cnt = 0;
//     int pidp_cnt = 0;
//     int pidy_cnt = 0;
//     int pids_cnt = 0;

    while(parser.next_message(msg)) {
        auto name = parser.get_message_name(msg);
        int instance = -1;
        parser.get_scalar_field(msg, "Instance", instance);

        bool in_whitelist = false;

        in_whitelist = in_whitelist || name == "FMT";
        in_whitelist = in_whitelist || name == "FMTU";
        in_whitelist = in_whitelist || name == "PARM";
        in_whitelist = in_whitelist || name == "GPS";
        in_whitelist = in_whitelist || name == "CMD";
        in_whitelist = in_whitelist || name == "MSG";
        in_whitelist = in_whitelist || name == "MODE";
        in_whitelist = in_whitelist || name == "AHR2";
        in_whitelist = in_whitelist || name == "ATT";
        in_whitelist = in_whitelist || name == "POS";

        if (!in_whitelist) {
            continue;
        }
//         if (name == "IMU2" || name == "IMU3") {
//             continue;
//         }
//         if (name == "NKF1" || name == "NKF2" || name == "NKF3" || name == "NKF4" || name == "NKF5" || name == "NKQ") {
//             if (instance != 0) {
//                 continue;
//             }
//         }
//
//         if (name == "SONR") {
//             if (sonr_cnt >= 5) {
//                 sonr_cnt = 0;
//             } else {
//                 sonr_cnt++;
//                 continue;
//             }
//         }
//
//         if (name == "NTUN") {
//             if (ntun_cnt >= 2) {
//                 ntun_cnt = 0;
//             } else {
//                 ntun_cnt++;
//                 continue;
//             }
//         }
//
//         if (name == "BAT" && instance != -1) {
//             if (bat_cnt[instance] >= 5) {
//                 bat_cnt[instance] = 0;
//             } else {
//                 bat_cnt[instance]++;
//                 continue;
//             }
//         }
//
//         if (name == "TPFF") {
//             if (tpff_cnt >= 5) {
//                 tpff_cnt = 0;
//             } else {
//                 tpff_cnt++;
//                 continue;
//             }
//         }
//
//         if (name == "AHR2") {
//             if (ahr2_cnt >= 2) {
//                 ahr2_cnt = 0;
//             } else {
//                 ahr2_cnt++;
//                 continue;
//             }
//         }
//
//         if (name == "PIDR") {
//             if (pidr_cnt >= 3) {
//                 pidr_cnt = 0;
//             } else {
//                 pidr_cnt++;
//                 continue;
//             }
//         }
//
//         if (name == "PIDP") {
//             if (pidp_cnt >= 3) {
//                 pidp_cnt = 0;
//             } else {
//                 pidp_cnt++;
//                 continue;
//             }
//         }
//
//         if (name == "PIDY") {
//             if (pidy_cnt >= 3) {
//                 pidy_cnt = 0;
//             } else {
//                 pidy_cnt++;
//                 continue;
//             }
//         }
//
//         if (name == "PIDS") {
//             if (pids_cnt >= 3) {
//                 pids_cnt = 0;
//             } else {
//                 pids_cnt++;
//                 continue;
//             }
//         }


        fwrite(parser.get_message_pointer_including_header(msg), parser.get_message_size_including_header(msg), 1, outfile);
    }

    fclose(outfile);
    return 0;
}
