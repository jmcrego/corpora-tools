#include <iostream>
#include <fstream>
#include <cstdlib>
#include <vector>
#include <set>
#include "LCS.h"
#include "Tools.h"

void usage(std::string name){
  std::cerr << "usage: " << name << " -s FILE -t FILE [-v]" << std::endl;
  std::cerr << "   -s      FILE : train src file" << std::endl;
  std::cerr << "   -t      FILE : train tgt file" << std::endl;
  return;
}

int main(int argc, char** argv) {
  std::string sepwords = " ";
  bool verbose = false;
  std::string fsrc = "";
  std::string ftgt = "";
  for (size_t i = 1; i < argc; i++){
    std::string tok = argv[i];
    if (tok == "-s" and i<argc) { i++; fsrc = argv[i]; }
    else if (tok == "-t" and i<argc) { i++; ftgt = argv[i]; }
    else if (tok == "-v") { verbose = true; }
    else if (tok == "-h") {
      usage(argv[0]);
      return 1;      
    }
    else{
      std::cerr << "error: unknown option!" << tok << std::endl;
      usage(argv[0]);
      return 1;
    }
  }
  if (fsrc.size() == 0 || ftgt.size() == 0){
      std::cerr << "error: input files are needed!" << std::endl;
      usage(argv[0]);
      return 1;    
  }

  std::vector<std::string> vsrc, vtgt;
  if (! load(fsrc,vsrc)) return 1;
  if (! load(ftgt,vtgt)) return 1;
  if (vsrc.size() != vtgt.size()){
    std::cerr << "error: input files with different sizes!" << std::endl;
    return 1;
  }

  for (size_t i = 0; i< vsrc.size(); i++){
    std::vector<std::string> S = split(vsrc[i],sepwords,false);
    std::vector<std::string> T = split(vtgt[i],sepwords,false);
    if (verbose) {
      std::cout << "i: " << i << std::endl;
      std::cout << "S: " << vsrc[i] << std::endl;
      std::cout << "T: " << vtgt[i] << std::endl;
    }
    LCS lcs(S,T);
    std::vector<std::string> v = lcs.lcs;
    /*** write sentences in corresponding files ***************/
    for (size_t j=0; j<v.size(); j++){
      std::cout << (j?" ":"") << v[j];
    }
    std::cout << std::endl;
  }

  return 0;
}
