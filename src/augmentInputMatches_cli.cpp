#include <iostream>
#include <fstream>
#include <cstdlib>
#include <vector>
#include <set>
#include "LCS.h"
#include "Align.h"
#include "Tools.h"

void related(std::vector<std::string> X, std::vector<std::string> S, std::vector<std::string> T, std::vector<std::string> A, std::vector<bool>& x_related, std::vector<bool>& t_related, bool verbose) {
  LCS lcs(X,S);
  Align ali(A,S.size(),T.size());
  std::vector<std::set<size_t> > s2x = lcs.y2x;
  std::vector<std::set<size_t> > t2s = ali.y2x;

  for (size_t t=0 ; t<T.size(); t++){
    bool all_related = true; //all alignments of this t must be aligned to s's related to x
    for (std::set<size_t>::iterator it_s=t2s[t].begin(); it_s!=t2s[t].end(); ++it_s){
      if (s2x[*it_s].size() == 0){ //this s is not related to any x
        all_related = false;
        break;  
      }
    }   
    if (all_related && t2s[t].size() > 0){ //at least one alignment
      t_related[t] = true;
      for (std::set<size_t>::iterator it_s=t2s[t].begin(); it_s!=t2s[t].end(); ++it_s){
        for (std::set<size_t>::iterator it_x=s2x[*it_s].begin(); it_x!=s2x[*it_s].end(); ++it_x){
          x_related[*it_x] = true;
        }
      }
    }
  }
  return;
}

void buildfactors(std::vector<std::string> X, std::vector<std::string> T,std::vector<bool> x_related, std::vector<bool> t_related, std::vector<std::string>& vf1, std::vector<std::string>& vf2, bool embedding, std::string tagS, std::string tagC, std::string tagT, std::string tagU, std::string tagE, std::string sepsents){
  for (size_t i=0; i<X.size(); i++){
    vf1.push_back(X[i]);
    if (embedding) vf2.push_back(tagS);
    else{
      if (x_related[i]) vf2.push_back(tagC); 
      else vf2.push_back(tagS);
    }
  }
  vf1.push_back(sepsents);
  vf2.push_back(sepsents);
  for (size_t i=0; i<T.size(); i++){
    vf1.push_back(T[i]);
    if (embedding) vf2.push_back(tagE);
    else{
      if (t_related[i]) vf2.push_back(tagT); 
      else vf2.push_back(tagU);
    }
  }
  return;
}

void usage(std::string name){
  std::cerr << "usage: " << name << " -o FILE -s FILE -t FILE -a FILE -tst FILE -match FILE [-colI INT] [-colS INT] [-sep STRING] [-v]" << std::endl;
  std::cerr << "   -o      FILE : output file (FILE.f1 and FILE.f2 are created)" << std::endl;
  std::cerr << "   -s      FILE : train src file" << std::endl;
  std::cerr << "   -t      FILE : train tgt file" << std::endl;
  std::cerr << "   -a      FILE : train ali file" << std::endl;
  std::cerr << "   -tst    FILE : test source file" << std::endl;
  std::cerr << "   -match  FILE : test match file" << std::endl;
  std::cerr << "   -colI    INT : column where match index is found (default 0)" << std::endl;
  std::cerr << "   -colS    INT : column where match score is found (default -1:not used)" << std::endl;
  std::cerr << "   -minS  FLOAT : minimu score to consider a match (default 0.0)" << std::endl;
  std::cerr << "   -embedding   : do not perform alignments (uses tag E)" << std::endl;
  std::cerr << "   -sep  STRING : token used to mark sentence boundary (default ‖)" << std::endl;
  std::cerr << "   -tagS STRING : replace tag S by STRING" << std::endl;
  std::cerr << "   -tagC STRING : replace tag C by STRING" << std::endl;
  std::cerr << "   -tagT STRING : replace tag T by STRING" << std::endl;
  std::cerr << "   -tagU STRING : replace tag U by STRING" << std::endl;
  std::cerr << "   -tagE STRING : replace tag E by STRING" << std::endl;
  std::cerr << "   -v           : verbose output" << std::endl;
  std::cerr << std::endl;
  std::cerr << "Tags used:" << std::endl;
  std::cerr << "S: source words without related target (to be freely translated)" << std::endl;
  std::cerr << "C: source words with related target (to copy an augmented target word)" << std::endl;
  std::cerr << "T: target words with related source (part of the match)" << std::endl;
  std::cerr << "U: target words without related source (not in the match)" << std::endl;
  std::cerr << "E: target words from similar sentence found using embeddings (no alignments performed)" << std::endl;
  std::cerr << "Comments:" << std::endl;
  std::cerr << "All files must be lightly tokenised (split punctuation)" << std::endl;

  return;
}

int main(int argc, char** argv) {
  bool verbose = false;
  std::string fsrc = "";
  std::string ftgt = "";
  std::string fali = "";
  std::string ftst = "";
  std::string fout = "";
  std::string fmatch = "";
  std::string sepwords = " ";
  std::string sepsents = "‖";
  bool embedding = false;
  std::string tagS = "S";
  std::string tagC = "C";
  std::string tagT = "T";
  std::string tagU = "U";
  std::string tagE = "E";
  size_t colI = 0;
  int colS = -1;
  float minS = 0.0;
  for (size_t i = 1; i < argc; i++){
    std::string tok = argv[i];
    if (tok == "-s" and i<argc) { i++; fsrc = argv[i]; }
    else if (tok == "-t" and i<argc) { i++; ftgt = argv[i]; }
    else if (tok == "-a" and i<argc) { i++; fali = argv[i]; }
    else if (tok == "-tst" and i<argc) { i++; ftst = argv[i]; }
    else if (tok == "-match" and i<argc) { i++; fmatch = argv[i]; }
    else if (tok == "-colI" and i<argc) { i++; colI = std::atoi(argv[i]); }
    else if (tok == "-colS" and i<argc) { i++; colS = std::atoi(argv[i]); }
    else if (tok == "-minS" and i<argc) { i++; minS = std::atof(argv[i]); }
    else if (tok == "-o" and i<argc) { i++; fout = argv[i]; }
    else if (tok == "-sep" and i<argc) { i++; sepsents = argv[i]; }
    else if (tok == "-tagS" and i<argc) { i++; tagS = argv[i]; }
    else if (tok == "-tagC" and i<argc) { i++; tagC = argv[i]; }
    else if (tok == "-tagT" and i<argc) { i++; tagT = argv[i]; }
    else if (tok == "-tagU" and i<argc) { i++; tagU = argv[i]; }
    else if (tok == "-tagE" and i<argc) { i++; tagE = argv[i]; }
    else if (tok == "-embedding") { embedding = true; }
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
      std::cerr << "error: train files are needed!" << std::endl;
      usage(argv[0]);
      return 1;    
  }
  if (ftst.size() == 0 || fmatch.size() == 0){
      std::cerr << "error: test files are needed!" << std::endl;
      usage(argv[0]);
      return 1;    
  }
  if (fout.size() == 0){
      std::cerr << "error: output file is needed!" << std::endl;
      usage(argv[0]);
      return 1;    
  }

  std::vector<std::string> vsrc, vtgt, vali, vtst, vmatch;
  if (! load(fsrc,vsrc)) return 1;
  if (! load(ftgt,vtgt)) return 1;
  if (! load(fali,vali)) return 1;
  if (vsrc.size() != vtgt.size() || vsrc.size() != vali.size()){
    std::cerr << "error: train files with different sizes!" << std::endl;
    return 1;
  }
  if (! load(ftst,vtst)) return 1;
  if (! load(fmatch,vmatch)) return 1;
  if (vtst.size() != vmatch.size()){
    std::cerr << "error: test/match files with different sizes!" << std::endl;
    return 1;
  }

  std::ofstream of1;
  of1.open((fout+".f1").c_str(), std::ofstream::out);
  std::ofstream of2;
  of2.open((fout+".f2").c_str(), std::ofstream::out);

  for (size_t i = 0; i< vtst.size(); i++){
    if (verbose){
      std::cout << "i=" << i << std::endl;
      std::cout << "X: " << vtst[i] << std::endl;
    }
    std::vector<std::string> X = split(vtst[i],sepwords,false);
    std::vector<std::string> cols = split(vmatch[i],"\t",false);
    std::vector<std::string> vf1;
    std::vector<std::string> vf2;
    /*** there is no match ********************/
    if (cols.size() < colI+1){
      if (verbose) std::cout << "no match" << std::endl;
    }
    /*** there is a match ********************/
    else {
      size_t j = std::atoi(cols[colI].c_str()) - 1;
      if (j >= vsrc.size()){
	std::cerr << "error: match out of bounds!" << std::endl;
	return 1;
      }
      float score = 9999.0; //highest score if it is not given in file
      if (colS >= 0){
	score = std::atof(cols[colS].c_str());
      }
      if (score >= minS){
	std::vector<std::string> S = split(vsrc[j],sepwords,false);
	std::vector<std::string> T = split(vtgt[j],sepwords,false);
	std::vector<std::string> A = split(vali[j],sepwords,false);
	if (verbose) {
	  std::cout << "match=" << j << std::endl;
	  std::cout << "S: " << vsrc[j] << std::endl;
	  std::cout << "T: " << vtgt[j] << std::endl;
	  std::cout << "A: " << vali[j] << std::endl;
	}
	std::vector<bool> x_related(X.size(),false);
	std::vector<bool> t_related(T.size(),false);
	if (! embedding) related(X,S,T,A,x_related,t_related,verbose);
	buildfactors(X,T,x_related,t_related,vf1,vf2,embedding,tagS,tagC,tagT,tagU,tagE,sepsents);
      }
      else{
	if (verbose) std::cout << "low match" << std::endl;
      }
    }
    /*** write sentences in corresponding files ***************/
    if (verbose) std::cout << "AUGMENTED:";
    for (size_t i=0; i<vf1.size(); i++){
      of1 << (i?" ":"") << vf1[i];
      of2 << (i?" ":"") << vf2[i];
      if (verbose) std::cout << " " << vf1[i] << ":" << vf2[i];
    }
    of1 << std::endl;
    of2 << std::endl;
    if (verbose) std::cout << std::endl;
  }

  of1.close();
  of2.close();

  return 0;
}
