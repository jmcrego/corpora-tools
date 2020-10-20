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
  std::cerr << "   -l       INT : max phrase length (default 7)" << std::endl;
  return;
}

int main(int argc, char** argv) {
  std::string space="＿";
  std::string idwrd="．";
  std::string trad="‖";
  std::string sepwords = " ";
  bool verbose = false;
  std::string fsrc = "";
  std::string ftgt = "";
  std::string fali = "";
  size_t maxl = 7;
  for (size_t i = 1; i < argc; i++){
    std::string tok = argv[i];
    if (tok == "-s" and i<argc) { i++; fsrc = argv[i]; }
    else if (tok == "-t" and i<argc) { i++; ftgt = argv[i]; }
    else if (tok == "-a" and i<argc) { i++; fali = argv[i]; }
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

  for (size_t i = 0; i< vsrc.size(); i++){
    std::vector<std::string> S = split(vsrc[i],sepwords,false);
    std::vector<std::string> T = split(vtgt[i],sepwords,false);
    std::vector<std::string> A = split(vali[i],sepwords,false);
    if (verbose) {
      std::cout << "i: " << i << std::endl;
      std::cout << "S: " << vsrc[i] << std::endl;
      std::cout << "T: " << vtgt[i] << std::endl;
      std::cout << "A: " << vali[i] << std::endl;
    }
    Align a(A,S.size(),T.size());
    for (size_t s_min=0; s_min<S.size(); s_min++){
      for (size_t s_max=s_min; s_max<S.size(); s_max++){
        if s_max-s_min >= maxl break; //source_phrase exceeds phrase length -l
        std::set<size_t> phrase_t = a.phrase_t(s_min,s_max)
        if phrase_t.empty() continue; //source_phrase has no alignments
        t_min = *(phrase_t.begin());
        t_max = *(phrase_t.rbegin());
        std::set<size_t> phrase_s = a.phrase_t(t_min,t_max)
        if *(phrase_s.begin()) != s_min break; // current phrase_t points to an s < s_min
        if *(phrase_s.rbegin()) != s_max continue; // current phrase_t points to an s > s_max
        std::vector<std::vector> > phrases=a.extend_phrases(s_min, s_max, t_min, t_max);
        for (it=phrases.begin(); it!=phrases.end(); it++){
          s_from = *it[0];
          s_to = *it[1];
          t_from = *it[2];
          t_to = *it[3];
          for (size_t s=s_from; s<=s_to; s++)
            std::cout << (s!=s_from?space:"") << S[s];
          std::cout << trad;
          for (size_t t=t_from; t<=t_to; t++)
            std::cout << (t!=t_from?space:"") << T[t];
          std::cout << std::endl;
        }
    }




/*
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
*/
  return 0;
}
