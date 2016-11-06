/* quickstartindex.cc: Simplest possible indexer */

#include <xapian.h>
#include <iostream>
#include <string>
#include <vector>
#include <cctype>
#include <algorithm>

using namespace std;

#define MAX_KEY 230

#define SPLIT_TITLE_INTO_KEYWORDS

// Split a string into its tokens, based on the given delimiters
void Tokenize(const string& str, vector<string>& tokens, 
              const string& delimiters)
{
    // Skip delimiters at beginning.
    string::size_type lastPos = str.find_first_not_of(delimiters, 0);
    // Find first "non-delimiter".
    string::size_type pos     = str.find_first_of(delimiters, lastPos);

    while (string::npos != pos || string::npos != lastPos)
    {
        // Found a token, add it to the vector.
        tokens.push_back(str.substr(lastPos, pos - lastPos));
        // Skip delimiters.  Note the "not_of"
        lastPos = str.find_first_not_of(delimiters, pos);
        // Find next "non-delimiter"
        pos = str.find_first_of(delimiters, lastPos);
    }
}

// We will perform case insensitive searches, 
// so we need a function to lowcase() a string
char to_lower (const char c) { return tolower(c); }
void lowcase(string& s) { transform(s.begin(), s.end(), s.begin(), to_lower); }

int main(int argc, char **argv)
{
    unsigned total = 0;
    try {
        // Make the database
        Xapian::WritableDatabase database("db/", Xapian::DB_CREATE_OR_OPEN);

        string docId;
        while(1) {
            string title;
            if (cin.eof()) break;
            getline(cin, title);
            int l = title.length();
            if (l>4 && title[0] == '#' && title.substr(l-4, 4) == ".bz2") {
                docId = title.substr(1, string::npos);  
                continue;
            }

            string Title = title;
            lowcase(title);

            // Make the document
            Xapian::Document newdocument;

            // Target: filename and the exact title used
            string target = docId + string(":") + Title;
            if (target.length()>MAX_KEY)
                target = target.substr(0, MAX_KEY);
            newdocument.set_data(target);

            // 1st Source: the lowercased title
            if (title.length() > MAX_KEY)
                title = title.substr(0, MAX_KEY);
            newdocument.add_posting(title.c_str(), 1);

            vector<string> keywords;
            Tokenize(title, keywords, " ");

            // 2nd source: All the title's lowercased words
            int cnt = 2;
            for (vector<string>::iterator it=keywords.begin(); 
                it!=keywords.end(); it++) 
            {
                if (it->length() > MAX_KEY)
                    *it = it->substr(0, MAX_KEY);
                newdocument.add_posting(it->c_str(), cnt++);
            }

            try {
                //cout << "Added " << title << endl;
                // Add the document to the database
                database.add_document(newdocument);
            } catch(const Xapian::Error &error) {
                cout << "Exception: "  << error.get_msg();
                cout << "\nWhen adding:\n" << title;
                cout << "\nOf length " << title.length() << endl;
            }
            total ++;

            if ((total % 8192) == 0) {
                cout << total << " articles indexed so far" << endl;
            }
        }
    } catch(const Xapian::Error &error) {
        cout << "Exception: "  << error.get_msg() << endl;
    }
    cout << total << " articles indexed." << endl;
}
