#ifndef TOOLS_H    // To make sure you don't declare the function more than once by including the header multiple times.
#define TOOLS_H
//g++ -c Tools.cpp

std::vector<std::string> split(std::string, std::string, bool);
bool load(std::string, std::vector<std::string>&);

#endif
