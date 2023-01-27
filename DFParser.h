#pragma once

#include <boost/algorithm/string/classification.hpp> // Include boost::for is_any_of
#include <boost/algorithm/string/split.hpp> // Include for boost::split
#include <iostream>
#include <string>
#include <iomanip>
#include <sstream>
#include <vector>
#include <map>

using namespace std;

#define HEAD_BYTE1  0xA3    // Decimal 163
#define HEAD_BYTE2  0x95    // Decimal 149

class DFLogParser {
public:
    typedef struct {
        typedef struct {
            char typechar;
            string name;
            int ofs;
            int len;
        } Field;

        uint8_t type;
        string name;
        int len;
        vector<Field> fields;
    } Format;

    DFLogParser(istream& infile) : _if(infile) {
        _formats[0x80] = {
            0x80,
            "FMT",
            89,
            {
                {'B',"Type",0,1},
                {'B',"Length",1,1},
                {'n',"Name",2,4},
                {'N',"Format",6,16},
                {'Z',"Columns",22,64}
            }
        };
    }

    Format::Field* get_field_definition(int type, const string& fieldname) {
        auto& fields = _formats[type].fields;
        for (auto& f : fields) {
            if (f.name == fieldname) {
                return &f;
            }
        }
        return NULL;
    }

    template <typename T>
    bool get_scalar_field(int type, const string& fieldname, const vector<uint8_t>& msgbody, T& ret) {
        Format::Field* field_ptr = get_field_definition(type, fieldname);
        if (!field_ptr) return false;
        Format::Field& field = *field_ptr;

        switch(field.typechar) {
            case 'B':
            case 'M':
                ret = (T)*reinterpret_cast<const uint8_t*>(&msgbody.data()[field.ofs]);
                return true;
            case 'b':
                ret = (T)*reinterpret_cast<const int8_t*>(&msgbody.data()[field.ofs]);
                return true;
            case 'h':
                ret = (T)*reinterpret_cast<const int16_t*>(&msgbody.data()[field.ofs]);
                return true;
            case 'H':
                ret = (T)*reinterpret_cast<const uint16_t*>(&msgbody.data()[field.ofs]);
                return true;
            case 'i':
                ret = (T)*reinterpret_cast<const int32_t*>(&msgbody.data()[field.ofs]);
                return true;
            case 'I':
                ret = (T)*reinterpret_cast<const uint32_t*>(&msgbody.data()[field.ofs]);
                return true;
            case 'q':
                ret = (T)*reinterpret_cast<const int64_t*>(&msgbody.data()[field.ofs]);
                return true;
            case 'Q':
                ret = (T)*reinterpret_cast<const uint64_t*>(&msgbody.data()[field.ofs]);
                return true;
            case 'f':
                ret = (T)*reinterpret_cast<const float*>(&msgbody.data()[field.ofs]);
                return true;
            case 'L':
                ret = (T)*reinterpret_cast<const uint32_t*>(&msgbody.data()[field.ofs]);
                ret /= 1e7;
                return true;
            case 'd':
                ret = (T)*reinterpret_cast<const double*>(&msgbody.data()[field.ofs]);
                return true;
            case 'c':
                ret = (T)*reinterpret_cast<const int16_t*>(&msgbody.data()[field.ofs]);
                ret /= 100;
                return true;
            case 'C':
                ret = (T)*reinterpret_cast<const uint16_t*>(&msgbody.data()[field.ofs]);
                ret /= 100;
                return true;
            case 'e':
                ret = (T)*reinterpret_cast<const int32_t*>(&msgbody.data()[field.ofs]);
                ret /= 100;
                return true;
            case 'E':
                ret = (T)*reinterpret_cast<const uint32_t*>(&msgbody.data()[field.ofs]);
                ret /= 100;
                return true;
        }
        return false;
    }
    template<typename T> bool get_scalar_field(int type, const string& fieldname, const vector<uint8_t>& msgbody, uint8_t& ret);
    template<typename T> bool get_scalar_field(int type, const string& fieldname, const vector<uint8_t>& msgbody, int8_t& ret);
    template<typename T> bool get_scalar_field(int type, const string& fieldname, const vector<uint8_t>& msgbody, uint16_t& ret);
    template<typename T> bool get_scalar_field(int type, const string& fieldname, const vector<uint8_t>& msgbody, int16_t& ret);
    template<typename T> bool get_scalar_field(int type, const string& fieldname, const vector<uint8_t>& msgbody, uint32_t& ret);
    template<typename T> bool get_scalar_field(int type, const string& fieldname, const vector<uint8_t>& msgbody, int32_t& ret);
    template<typename T> bool get_scalar_field(int type, const string& fieldname, const vector<uint8_t>& msgbody, int64_t& ret);
    template<typename T> bool get_scalar_field(int type, const string& fieldname, const vector<uint8_t>& msgbody, uint64_t& ret);

    bool get_string_field(int type, const string& fieldname, const vector<uint8_t>& msgbody, string& ret) {
        Format::Field* field_ptr = get_field_definition(type, fieldname);
        if (!field_ptr) return false;
        Format::Field& field = *field_ptr;

        switch(field.typechar) {
            case 'n':
            case 'N':
            case 'Z': {
                ret = "";
                for (int i=field.ofs; i<field.ofs+field.len; i++) {
                    if (msgbody[i] == 0) break;
                    ret.push_back((char)msgbody[i]);
                }
                return true;
            }
        }
        return false;
    }

    void process_fmt(const vector<uint8_t>& msgbody) {
        Format new_format;

        get_scalar_field(0x80, "Type", msgbody, new_format.type);
        get_scalar_field(0x80, "Length", msgbody, new_format.len);

        get_string_field(0x80, "Name", msgbody, new_format.name);
        string fmtstr;
        get_string_field(0x80, "Format", msgbody, fmtstr);
        vector<string> fieldnames;

        string colstr;
        get_string_field(0x80, "Columns", msgbody, colstr);
        boost::split(fieldnames, colstr, boost::is_any_of(","));

        assert(fieldnames.size() == fmtstr.length());

        int ofs = 0;
        for (int i=0; i<fieldnames.size(); i++) {
            int size =  _fieldsizemap[fmtstr[i]];
            new_format.fields.push_back({fmtstr[i], fieldnames[i], ofs, size});
            ofs += size;
        }
        cout << new_format.name << " " << fmtstr << " " << ofs << " " << new_format.len-3 << endl;
        assert(ofs == new_format.len-3);
        _formats[int(new_format.type)] = new_format;
    }

    bool next_msg_body(uint8_t& type, vector<uint8_t>& msgbody) {
        msgbody.clear();

        uint8_t header[3];
        _if.read((char*)header, 3);

        int skip_count = 0;
        stringstream bytes;
        while (header[0] != HEAD_BYTE1 || header[1] != HEAD_BYTE2 || (_formats.find(header[2]) == _formats.end())) {
            bytes << " " << setw(2) << setfill('0') << hex << (int)header[0];
            skip_count++;
            _if.seekg(-2,_if.cur);
            if (!_if.read((char*)header, 3)) {
                cout << "read failed 1" << endl;
                return false;
            }
        }
        if (skip_count > 0) {
            cerr << "skipped " << skip_count << " bytes: " << bytes.str() << endl;
        }

        type = header[2];

        int body_len = _formats[type].len-3;

        msgbody.resize(body_len);

        if(!_if.read(reinterpret_cast<char*>(msgbody.data()), body_len)) {
            cout << "read failed" << endl;
            return false;
        }

        if (type == 0x80) {
            process_fmt(msgbody);
        }

        return true;
    }

private:

    typedef struct {
        uint8_t type;
        vector<uint8_t> data;
    } message_t;
    istream& _if;
    map<uint8_t,Format> _formats;

    map<char,uint8_t> _fieldsizemap = {
        {'b', 1},
        {'B', 1},
        {'M', 1},
        {'h', 2},
        {'H', 2},
        {'i', 4},
        {'I', 4},
        {'q', 8},
        {'Q', 8},
        {'n', 4},
        {'N', 16},
        {'Z', 64},
        {'c', 2},
        {'C', 2},
        {'e', 4},
        {'E', 4},
        {'f', 4},
        {'d', 8},
        {'L', 4},
        {'a', 64}
    };
};
