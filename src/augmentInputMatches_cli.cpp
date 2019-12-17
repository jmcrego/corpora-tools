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

void buildfactors(std::vector<std::string> X, std::vector<std::string> T,std::vector<bool> x_related, std::vector<bool> t_related, std::vector<std::string>& vf1, std::vector<std::string>& vf2, bool tagC, bool tagU, bool tagE, std::string sepsents){
  std::string strS = "S";
  std::string strT = "T";
  std::string strC = "S";
  std::string strU = "T";
  std::string strE = "E";
  if (tagC) std::string strC = "C";
  if (tagU) std::string strU = "U";

  for (size_t i=0; i<X.size(); i++){
    vf1.push_back(X[i]);
    if (tagE) vf2.push_back(strS);
    else{
      if (x_related[i]) vf2.push_back(strC); 
      else vf2.push_back(strS);
    }
  }
  vf1.push_back(sepsents);
  vf2.push_back(sepsents);
  for (size_t i=0; i<T.size(); i++){
    vf1.push_back(T[i]);
    if (tagE) vf2.push_back(strE);
    else{
      if (t_related[i]) vf2.push_back(strT); 
      else vf2.push_back(strU);
    }
  }
  return;
}

float ratio_tmatch(std::vector<bool> t_related, std::vector<std::string> T, std::vector<std::string> R, bool tagU){
  std::set<std::string> setR;
  for (size_t i=0; i<R.size(); i++) setR.insert(R[i]);
  size_t total = 0;
  size_t in_match = 0;
  for (size_t i=0; i<T.size(); i++){
    if (!tagU or t_related[i]){ //if !tagU all words are considered related (marked with T)
      total += 1;
      std::cout << T[i];
      if (setR.find(T[i]) != setR.end()){
	in_match += 1;
	std::cout << " appear!";
      }
      std::cout << std::endl;
    }
  }
  if (total == 0) return 0.0; //all T words are no related (wont be filtered out)
  return (float)in_match/(float)total; //ratio is lower
}

void usage(std::string name){
  std::cerr << "usage: " << name << " -o FILE -s FILE -t FILE -a FILE -tst FILE [-ref FILE] -match FILE [-colI INT] [-colS INT] [-tagC] [-tagU] [-tagE] [-sep STRING] [-v]" << std::endl;
  std::cerr << "   -o       FILE : output file (FILE.f1 and FILE.f2 are created)" << std::endl;
  std::cerr << "   -s       FILE : train src file" << std::endl;
  std::cerr << "   -t       FILE : train tgt file" << std::endl;
  std::cerr << "   -a       FILE : train ali file" << std::endl;
  std::cerr << "   -tst     FILE : test source file" << std::endl;
  std::cerr << "   -ref     FILE : test reference file" << std::endl;
  std::cerr << "   -match   FILE : test match file" << std::endl;
  std::cerr << "   -colI     INT : column where match index is found (default 0)" << std::endl;
  std::cerr << "   -colS     INT : column where match score is found (default -1:not used)" << std::endl;
  std::cerr << "   -minS   FLOAT : minimu score to consider a match (default 0.0)" << std::endl;
  std::cerr << "   -sep   STRING : token used to mark sentence boundary (default ‖)" << std::endl;
  std::cerr << "   -tagC         : use tag C to mark source words appearing in match (copy)" << std::endl;
  std::cerr << "   -tagU         : use tag U to mark target words not present in match (unrelated)" << std::endl;
  std::cerr << "   -tagE         : use tag E to mark all target words from embedding match (embedding)" << std::endl;
  std::cerr << "   -ratio  FLOAT : keep match if ratio of words marked T appearing in reference are at least FLOAT (default 0.0:not used)" << std::endl;
  std::cerr << "   -v            : verbose output" << std::endl;
  std::cerr << std::endl;
  std::cerr << "Comments:" << std::endl;
  std::cerr << "Option -tagE is used without options -tagC and -tagU" << std::endl;
  std::cerr << "Option -ratio is used with -ref option and without -tagE option" << std::endl;
  std::cerr << "All files must be lightly tokenised (split punctuation)" << std::endl;

  return;
}

int main(int argc, char** argv) {
  bool verbose = false;
  std::string fsrc = "";
  std::string ftgt = "";
  std::string fali = "";
  std::string ftst = "";
  std::string fref = "";
  std::string fout = "";
  std::string fmatch = "";
  std::string sepwords = " ";
  std::string sepsents = "‖";
  bool tagC = false;
  bool tagU = false;
  bool tagE = false;
  size_t colI = 0;
  int colS = -1;
  float minS = 0.0;
  std::string str_ratio = "0.0";
  for (size_t i = 1; i < argc; i++){
    std::string tok = argv[i];
    if (tok == "-s" and i<argc) { i++; fsrc = argv[i]; }
    else if (tok == "-t" and i<argc) { i++; ftgt = argv[i]; }
    else if (tok == "-a" and i<argc) { i++; fali = argv[i]; }
    else if (tok == "-tst" and i<argc) { i++; ftst = argv[i]; }
    else if (tok == "-ref" and i<argc) { i++; fref = argv[i]; }
    else if (tok == "-match" and i<argc) { i++; fmatch = argv[i]; }
    else if (tok == "-colI" and i<argc) { i++; colI = std::atoi(argv[i]); }
    else if (tok == "-colS" and i<argc) { i++; colS = std::atoi(argv[i]); }
    else if (tok == "-minS" and i<argc) { i++; minS = std::atof(argv[i]); }
    else if (tok == "-o" and i<argc) { i++; fout = argv[i]; }
    else if (tok == "-sep" and i<argc) { i++; sepsents = argv[i]; }
    else if (tok == "-tagC") { tagC = true; }
    else if (tok == "-tagU") { tagU = true; }
    else if (tok == "-tagE") { tagE = true; }
    else if (tok == "-ratio" and i<argc) { i++; str_ratio = argv[i]; }
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
  float ratio = std::atof(str_ratio.c_str()); 
  if (ratio > 1.0){
      std::cerr << "error: -ratio must be in range [0.0, 1.0]" << std::endl;
      usage(argv[0]);
      return 1;    
  }
  if (ratio > 0.0 && fref.size() == 0){
      std::cerr << "error: -ratio cannot be used without -ref option" << std::endl;
      usage(argv[0]);
      return 1;    
  }
  if (ratio > 0.0 && tagE){
      std::cerr << "error: -ratio cannot be used with -tagE option" << std::endl;
      usage(argv[0]);
      return 1;    
  }

  if (tagE && (tagC || tagU)){
      std::cerr << "error: -tagE cannot be used with options -tagC or -tagU" << std::endl;
      usage(argv[0]);
      return 1;    
  }
  
  std::vector<std::string> vsrc, vtgt, vali, vtst, vref, vmatch;
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
    std::cerr << "error: tst/match files with different sizes!" << std::endl;
    return 1;
  }
  if (fref.size() > 0){
    if (! load(fref,vref)) return 1;
    if (vtst.size() != vref.size()){
      std::cerr << "error: tst/ref files with different sizes!" << std::endl;
      return 1;
    }
  }

  std::cout << "vref.size=" << vref.size() << std::endl;

  std::string tags=".ratio"+str_ratio+".S";
  if (tagE){ //tags: ".SE"
    tags += "E";
  }
  else{ // tags: ".ST" or ".SCT" or ".STU" or ".SCTU"
    if (tagC) tags += "C";
    tags += "T";
    if (tagU) tags += "U";
  }
  fout += tags;

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
	std::vector<std::string> R;
	if (vref.size()) R = split(vref[i],sepwords,false);
	if (verbose) {
	  std::cout << "match=" << j << std::endl;
	  std::cout << "S: " << vsrc[j] << std::endl;
	  std::cout << "T: " << vtgt[j] << std::endl;
	  if (vref.size()) std::cout << "R: " << vref[i] << std::endl;
	  std::cout << "A: " << vali[j] << std::endl;
	}
	std::vector<bool> x_related(X.size(),false);
	std::vector<bool> t_related(T.size(),false);
	if (tagC or tagU){
	  related(X,S,T,A,x_related,t_related,verbose);
	}
	float r=1.0;
	if (!tagE && R.size()){
	  r = ratio_tmatch(t_related,T,R,tagU);
	  if (verbose) std::cout << "ratio=" << r << std::endl;
	}
	if (r >= ratio) buildfactors(X,T,x_related,t_related,vf1,vf2,tagC,tagU,tagE,sepsents);
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
