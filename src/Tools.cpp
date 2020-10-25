#include <iostream>
#include <fstream>
#include <vector>
#include "Tools.h"


std::vector<std::string> split(std::string str, std::string sep, bool allow_empty, std::string sepfactors="") {
  std::vector<std::string> v;
  size_t to;
  size_t from = 0;
  while ((to = str.find(sep,from)) != std::string::npos){
    if (allow_empty || to > from){
      v.push_back(str.substr(from, to-from));
      if (sepfactors.size()>0){
        size_t pos = v[v.size()-1].find_last_of(sepfactors);
        if (pos!=std::string::npos) v[v.size()-1] = v[v.size()-1].substr(pos+1);
      }
    }
    from = to + sep.length();
  }
  to = str.size();
  if (allow_empty || to > from){
    v.push_back(str.substr(from, to-from));
    if (sepfactors.size()>0){
      size_t pos = v[v.size()-1].find_last_of(sepfactors);
      if (pos!=std::string::npos) v[v.size()-1] = v[v.size()-1].substr(pos+1);
    }
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

