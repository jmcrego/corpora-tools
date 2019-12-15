#include <iostream>
#include <fstream>
#include <vector>
#include "Tools.h"


std::vector<std::string> split(std::string str, std::string sep, bool allow_empty) {
  std::vector<std::string> v;
  size_t to;
  size_t from = 0;
  while ((to = str.find(sep,from)) != std::string::npos){
    if (allow_empty || to > from){
      v.push_back(str.substr(from, to-from));
    }
    from = to + sep.length();
  }
  to = str.size();
  if (allow_empty || to > from){
    v.push_back(str.substr(from, to-from));
  }
  return v;
}

bool load(std::string file, std::vector<std::string>& v){
  std::string str;
  std::ifstream in(file.c_str());
  if(!in) { 
    std::cerr << "error: cannot open file: "<< file << std::endl; 
    return false; 
  }
  while (std::getline(in, str)) { 
    v.push_back(str); 
  }
  in.close();
  return true;
}

