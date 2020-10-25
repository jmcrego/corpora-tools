#include <iostream>
#include <fstream>
#include <cstdlib>
#include <vector>
#include <set>
#include <unordered_set>
#include "LCS.h"
#include "Align.h"
#include "Tools.h"

void usage(std::string name){
  std::cerr << "usage: " << name << " -s FILE -t FILE -a FILE [-v]" << std::endl;
  std::cerr << "   -s      FILE : train src file" << std::endl;
  std::cerr << "   -t      FILE : train tgt file" << std::endl;
  std::cerr << "   -a      FILE : train s2t alignment file" << std::endl;
  std::cerr << "   -l       INT : max phrase length (default 7)" << std::endl;
  std::cerr << "   -rs     FILE : source rules (not used)" << std::endl;
  std::cerr << "   -rt     FILE : target rules (not used)" << std::endl;
  return;
}

bool filter_rules(std::unordered_set<std::string> &rules, std::vector<std::string> &X, size_t min, size_t max){
  std::string slice=X[min];
  for (size_t i=min+1; i<=max; i++){
    slice += " ";
    slice += X[i];
  }
  if (rules.find(slice) != rules.end()) return false;
  return true;
}

int main(int argc, char** argv) {
  std::string trad=" ||| ";
  std::string septokens = " ";
  std::string sepfactors = "￨";
  bool verbose = false;
  std::string fsrc = "";
  std::string ftgt = "";
  std::string fali = "";
  size_t maxl = 7;
  std::string frsrc = "";
  std::string frtgt = "";
  for (size_t i = 1; i < argc; i++){
    std::string tok = argv[i];
    if (tok == "-s" and i<argc) { i++; fsrc = argv[i]; }
    else if (tok == "-t" and i<argc) { i++; ftgt = argv[i]; }
    else if (tok == "-a" and i<argc) { i++; fali = argv[i]; }
    else if (tok == "-rs" and i<argc) { i++; frsrc = argv[i]; }
    else if (tok == "-rt" and i<argc) { i++; frtgt = argv[i]; }
    else if (tok == "-l" and i<argc) { i++; maxl = std::atoi(argv[i]); }
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

  std::vector<std::string> vsrc, vtgt, vali;
  if (! load(fsrc,vsrc)) return 1;
  if (! load(ftgt,vtgt)) return 1;
  if (! load(fali,vali)) return 1;
  if (vsrc.size() != vtgt.size() || vsrc.size() != vali.size()){
    std::cerr << "error: input files with different sizes!" << std::endl;
    return 1;
  }

  std::unordered_set<std::string> srules;
  if (frsrc != ""){
    std::vector<std::string> vrsrc;
    if (! load(frsrc,vrsrc)) return 1;
    for (size_t i=0; i<vrsrc.size(); i++) srules.insert(vrsrc[i]);
  }
  std::unordered_set<std::string> trules;
  if (frtgt != ""){
    std::vector<std::string> vrtgt;
    if (! load(frtgt,vrtgt)) return 1;
    for (size_t i=0; i<vrtgt.size(); i++) trules.insert(vrtgt[i]);
  }

  for (size_t i = 0; i< vsrc.size(); i++){
    std::vector<std::string> S = split(vsrc[i],septokens,false,"");
    std::vector<std::string> T = split(vtgt[i],septokens,false,"");
    std::vector<std::string> A = split(vali[i],septokens,false,"");
    std::vector<std::string> rS;
    if (srules.size()) rS = split(vsrc[i],septokens,false,sepfactors);
    std::vector<std::string> rT;
    if (trules.size()) rT = split(vtgt[i],septokens,false,sepfactors);
    if (verbose) {
      std::cout << "i: " << i << std::endl;
      std::cout << "S[" << S.size() << "]: " << vsrc[i] << std::endl;
      std::cout << "T[" << T.size() << "]: " << vtgt[i] << std::endl;
      std::cout << "A: " << vali[i] << std::endl;
    }
    Align a(A,S.size(),T.size());
    for (size_t s_min=0; s_min<S.size(); s_min++){
      for (size_t s_max=s_min; s_max<S.size(); s_max++){
        if (s_max-s_min >= maxl) break; //source_phrase exceeds phrase length l (stop increasing s_max)
        std::set<size_t> phrase_t = a.phrase_t(s_min,s_max);
        if (phrase_t.empty()) continue; //source_phrase has no alignments
        size_t t_min = *(phrase_t.begin());
        size_t t_max = *(phrase_t.rbegin());
        if (t_max-t_min >= maxl) break; //target_phrase exceeds phrase length l (stop increasing s_max)
        std::set<size_t> phrase_s = a.phrase_s(t_min,t_max);
        if (*(phrase_s.begin()) != s_min) break; // current phrase_t points to an s < s_min
        if (*(phrase_s.rbegin()) != s_max) continue; // current phrase_t points to an s > s_max
        /******************************/
        /****** extended phrases ******/
        /******************************/
        std::vector<std::vector<size_t> > phrases=a.extend_phrase(s_min, s_max, t_min, t_max, verbose);
        for (std::vector<std::vector<size_t> >::iterator it=phrases.begin(); it!=phrases.end(); it++){
          std::vector<size_t> v = *it;
          if ( srules.size() and filter_rules(srules, rS, v[0], v[1]) ) continue;
          if ( trules.size() and filter_rules(trules, rT, v[2], v[3]) ) continue;
          for (size_t s=v[0]; s<=v[1]; s++) std::cout << (s!=v[0]?septokens:"") << S[s];
          std::cout << trad;
          for (size_t t=v[2]; t<=v[3]; t++) std::cout << (t!=v[2]?septokens:"") << T[t];
          std::cout << std::endl;
        }
      }
    }
  }
  return 0;
}
