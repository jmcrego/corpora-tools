#include <iostream>
#include <fstream>
#include <cstdlib>
#include <vector>
#include <set>
#include "LCS.h"
#include "Align.h"
#include "Tools.h"

void usage(std::string name){
  std::cerr << "usage: " << name << " -s FILE -t FILE -a FILE [-v]" << std::endl;
  std::cerr << "   -s      FILE : train src file" << std::endl;
  std::cerr << "   -t      FILE : train tgt file" << std::endl;
  std::cerr << "   -a      FILE : train s2t alignment file" << std::endl;
  std::cerr << "   -src_consec  : src words does not contain holes" << std::endl;
  std::cerr << "   -tgt_consec  : tgt words does not contain holes" << std::endl;
  return;
}

int main(int argc, char** argv) {
  std::string space="＿";
  std::string idwrd="．";
  std::string trad="‖";
  std::string sepwords = " ";
  bool verbose = false;
  bool src_consec = false;
  bool tgt_consec = false;
  std::string fsrc = "";
  std::string ftgt = "";
  std::string fali = "";
  for (size_t i = 1; i < argc; i++){
    std::string tok = argv[i];
    if (tok == "-s" and i<argc) { i++; fsrc = argv[i]; }
    else if (tok == "-t" and i<argc) { i++; ftgt = argv[i]; }
    else if (tok == "-a" and i<argc) { i++; fali = argv[i]; }
    else if (tok == "-src_consec") { src_consec = true; }
    else if (tok == "-tgt_consec") { tgt_consec = true; }
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
  if (fsrc.size() == 0 || ftgt.size() == 0 || fali.size() == 0){
      std::cerr << "error: input files are needed!" << std::endl;
      usage(argv[0]);
      return 1;    
  }
  if (src_consec && tgt_consec){
      std::cerr << "error: both src/tgt cannot be consecutive!" << std::endl;
      usage(argv[0]);
      return 1;    
  }

  std::vector<std::string> vsrc, vtgt, vali;
  if (! load(fsrc,vsrc)) return 1;
  if (! load(ftgt,vtgt)) return 1;
  if (! load(fali,vali)) return 1;
  if (vsrc.size() != vtgt.size() || vsrc.size() != vali.size()){
    std::cerr << "error: input files with different sizes!" << std::endl;
    return 1;
  }

  for (size_t i = 0; i< vsrc.size(); i++){
    std::vector<std::string> S = split(vsrc[i],sepwords,false,"");
    std::vector<std::string> T = split(vtgt[i],sepwords,false,"");
    std::vector<std::string> A = split(vali[i],sepwords,false,"");
    if (verbose) {
      std::cout << "i: " << i << std::endl;
      std::cout << "S: " << vsrc[i] << std::endl;
      std::cout << "T: " << vtgt[i] << std::endl;
      std::cout << "A: " << vali[i] << std::endl;
    }
    Align a(A,S.size(),T.size());
    std::vector<std::pair<std::set<size_t>, std::set<size_t> > > groups;
    if (tgt_consec)
      groups = a.Groups(false,true);
    else if (src_consec)
      groups = a.Groups(true,true);
    else
      groups = a.Groups(true,false);

    for (size_t g=0; g<groups.size(); g++){
      for (std::set<size_t>::iterator it_s=groups[g].first.begin(); it_s!=groups[g].first.end(); it_s++){
	std::cout << (it_s!=groups[g].first.begin()?space:"") << *it_s << idwrd << S[*it_s];
      }
      std::cout << trad;
      for (std::set<size_t>::iterator it_t=groups[g].second.begin(); it_t!=groups[g].second.end(); it_t++){
	std::cout << (it_t!=groups[g].second.begin()?space:"") << *it_t << idwrd << T[*it_t];
      }
      if (g<groups.size()-1) std::cout << " ";
    }
    std::cout << std::endl;
  }

  return 0;
}
