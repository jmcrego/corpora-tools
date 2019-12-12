#include <iostream>
#include <fstream>
#include <cstdlib>
#include <vector>
#include<set>

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

std::vector<std::pair<size_t,size_t> > LCS(std::vector<std::string> X, std::vector<std::string> Y) {
  std::vector<std::pair<size_t,size_t> > result;
  if (X.size() == 0 || Y.size() == 0) return result;
  std::string last_x = X.back();
  std::string last_y = Y.back();
  
  if (last_x == last_y) {
    X.pop_back(); 
    Y.pop_back();
    result = LCS(X, Y);
    result.push_back(std::make_pair(X.size(),Y.size()));
    return result;
  }
  
  X.pop_back();
  std::vector<std::pair<size_t,size_t> > v1 = LCS(X, Y);
  
  X.push_back(last_x);
  Y.pop_back();
  std::vector<std::pair<size_t,size_t> > v2 = LCS(X, Y);
  
  if (v1.size() > v2.size()) return v1;
  else return v2;
}

std::vector<std::pair<size_t,size_t> > ALI(std::vector<std::string> A) {
  std::vector<std::pair<size_t,size_t> > result;
  if (A.size() == 0) return result;
  for (size_t i=0; i<A.size(); i++){
    std::vector<std::string> st = split(A[i], "-", false);
    if (st.size() != 2 ){
      std::cerr << "error: bad alignment format: "<< A[i] << std::endl; 
      exit(1);
    }
    result.push_back(std::make_pair(std::atoi(st[0].c_str()),std::atoi(st[1].c_str())));
  }
  return result;
}

void lcs_ali(std::vector<std::string> X, std::vector<std::string> S, std::vector<std::string> T, std::vector<std::string> A, std::vector<bool>& x_related, std::vector<bool>& t_related, bool verbose) {
  std::vector<std::pair<size_t,size_t> > lcs_xs = LCS(X,S);
  std::vector<std::pair<size_t,size_t> > ali_st = ALI(A);
  std::set<size_t> myset;

  //build s2x (vector of ints)
  std::vector<std::set<size_t> > s2x(S.size(),myset); //fill of empty sets
  for (size_t i = 0; i < lcs_xs.size(); i++) {
    s2x[lcs_xs[i].second].insert(lcs_xs[i].first);
  }
  //build t2s (vector of sets)
  std::vector<std::set<size_t> > t2s(T.size(),myset); //fill of empty sets
  for (size_t i = 0; i < ali_st.size(); i++) {
    t2s[ali_st[i].second].insert(ali_st[i].first);
  }

  for (size_t t=0 ; t<T.size(); t++){
    bool all_related = true; //all alignments of this t must be to s which are related to x
    for (std::set<size_t>::iterator it=t2s[t].begin(); it!=t2s[t].end(); ++it){
      size_t s = *it;
      if (s2x[s].size() == 0){
        all_related = false;
        break;  
      }
    }   
    if (all_related && t2s[t].size() > 0){ //at least one alignment
      t_related[t] = true;
      for (std::set<size_t>::iterator it1=t2s[t].begin(); it1!=t2s[t].end(); ++it1){
        size_t s = *it1;
        for (std::set<size_t>::iterator it2=s2x[s].begin(); it2!=s2x[s].end(); ++it2){
          size_t x = *it2;
          x_related[x] = true;
        }
      }
    }
  }
  return;
}


void usage(std::string name){
  std::cerr << "usage: " << name << " -s FILE -t FILE -a FILE -tst FILE -match FILE -tag STRING [-sep STRING]" << std::endl;
  std::cerr << "   -s     FILE : train src file" << std::endl;
  std::cerr << "   -t     FILE : train tgt file" << std::endl;
  std::cerr << "   -a     FILE : train ali file" << std::endl;
  std::cerr << "   -tst   FILE : test source file" << std::endl;
  std::cerr << "   -match FILE : test match file" << std::endl;
  std::cerr << "   -col    INT : column where match index is found (default 0)" << std::endl;
  std::cerr << "   -tag STRING : characters to use {'S','C','T','U'} (default 'SCTU')" << std::endl;
  std::cerr << "   -o     FILE : output file" << std::endl;
  std::cerr << "   -sep STRING : word separator (default ' ')" << std::endl;
  std::cerr << "   -v          : verbose output" << std::endl;
  std::cerr << "" << std::endl;
  std::cerr << "'S' source words without related target (to be freely translated)" << std::endl;
  std::cerr << "'C' source words with related target (to copy some target word)" << std::endl;
  std::cerr << "'T' target words with related source (within the match)" << std::endl;
  std::cerr << "'U' target words without related source (without the match)" << std::endl;

  return;
}

bool load(std::string file, std::vector<std::string> v){
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
  std::cerr << "[" << v.size() << "] " << file << std::endl;
  return true;
}

int main(int argc, char** argv) {
  bool verbose = false;
  std::string fsrc = "";
  std::string ftgt = "";
  std::string fali = "";
  std::string ftst = "";
  std::string fout = "";
  std::string fmatch = "";
  std::string sep = " ";
  std::string tag = "SCTU";
  size_t col = 0;
  for (size_t i = 1; i < argc; i++){
    std::string tok = argv[i];
    if (tok == "-sep" and i<argc) { i++; sep = argv[i]; }
    else if (tok == "-s" and i<argc) { i++; fsrc = argv[i]; }
    else if (tok == "-t" and i<argc) { i++; ftgt = argv[i]; }
    else if (tok == "-a" and i<argc) { i++; fali = argv[i]; }
    else if (tok == "-tst" and i<argc) { i++; ftst = argv[i]; }
    else if (tok == "-match" and i<argc) { i++; fmatch = argv[i]; }
    else if (tok == "-col" and i<argc) { i++; col = std::atoi(argv[i]); }
    else if (tok == "-tag" and i<argc) { i++; tag = argv[i]; }
    else if (tok == "-o" and i<argc) { i++; fout = argv[i]; }
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

  bool doS = false;
  bool doC = false;
  bool doT = false;
  bool doU = false;
  for (size_t i = 0; i < tag.size(); i++){
    if (tag[i] == 'S') doS = true;
    else if (tag[i] == 'C') doC = true;
    else if (tag[i] == 'T') doT = true;
    else if (tag[i] == 'U') doU = true;
    else {
      std::cerr << "error: bad tag option!" << std::endl;
      usage(argv[0]);
      return 1;          
    }
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
    std::vector<std::string> X = split(vtst[i],sep,false);
    std::vector<std::string> cols = split(vmatch[i],"\t",false);
    size_t j = std::atoi(cols[col].c_str());
    if (j >= vsrc.size()){
      std::cerr << "error: match out of bounds!" << std::endl;
      return 1;
    }
    std::vector<std::string> S = split(vsrc[j],sep,false);      
    std::vector<std::string> T = split(vtgt[j],sep,false);      
    std::vector<std::string> A = split(vali[j],sep,false);      
    std::vector<bool> x_related(X.size(),false);
    std::vector<bool> t_related(T.size(),false);
    lcs_ali(X,S,T,A,x_related,t_related,verbose);

    for (size_t i=0; i<X.size(); i++){
      of1 << (i?" ":"") << X[i];
      if (x_related[i]){
	of2 << (i?" ":"") << "C";
      }
      else{
	of2 << (i?" ":"") << "S";
      }
    }
    of1 << " " << "@";
    of2 << " " << "@";
    for (size_t i=0; i<T.size(); i++){
      of1 << " " << T[i];
      if (t_related[i]){
	of2 << " " <<  "T";
      }
      else{
	of2 << " " << "U";
      }
    }
    of1 << std::endl;
    of2 << std::endl;
  }
  of1.close();
  of2.close();

  return 0;
}
