//to compile, use: g++ augmentInputMatches.cpp -o augmentInputMatches
#include <iostream>
#include <fstream>
#include <cstdlib>
#include <vector>
#include <set>

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

std::vector<std::pair<size_t,size_t> > LCS(std::vector<std::string> X, std::vector<std::string> Y,bool verbose){
  size_t x = X.size();
  size_t y = Y.size();
  size_t L[x+1][y+1];
  //find lcs
  for (int i=0; i<=x; i++) {
    for (int j=0; j<=y; j++) {
      if (i == 0 || j == 0) L[i][j] = 0;
      else if (X[i-1] == Y[j-1]) L[i][j] = L[i-1][j-1] + 1;
      else L[i][j] = std::max(L[i-1][j], L[i][j-1]);
    }
  }
  std::vector<std::pair<size_t,size_t> > lcs_xy;
  // Start from the right-most-bottom-most corner to recover lcs
  while (x > 0 && y > 0) {
    // if same, part of the result
    if (X[x-1] == Y[y-1]) {
      lcs_xy.insert(lcs_xy.begin(),std::make_pair(x-1,y-1));
      x--;
      y--;
    }
    // If not same, then find the larger of two and go in the direction of larger value
    else if (L[x-1][y] > L[x][y-1]) x--;
    else y--;
  }
  if (verbose){
    std::cout << "lcs";
    for (size_t i=0; i<lcs_xy.size(); i++) std::cout << " (" << lcs_xy[i].first << "," << lcs_xy[i].second << ")";
    std::cout << std::endl;
  }
  return lcs_xy;
}

std::vector<std::pair<size_t,size_t> > ALI(std::vector<std::string> A, bool verbose) {
  std::vector<std::pair<size_t,size_t> > ali_xy;
  if (A.size() == 0) return ali_xy;
  for (size_t i=0; i<A.size(); i++){
    std::vector<std::string> st = split(A[i], "-", false);
    if (st.size() != 2 ){
      std::cerr << "error: bad alignment format: "<< A[i] << std::endl; 
      exit(1);
    }
    ali_xy.push_back(std::make_pair(std::atoi(st[0].c_str()),std::atoi(st[1].c_str())));
  }
  if (verbose){
    std::cout << "ali";
    for (size_t i=0; i<ali_xy.size(); i++) std::cout << " (" << ali_xy[i].first << "," << ali_xy[i].second << ")";
    std::cout << std::endl;
  }
  return ali_xy;
}

void related(std::vector<std::string> X, std::vector<std::string> S, std::vector<std::string> T, std::vector<std::string> A, std::vector<bool>& x_related, std::vector<bool>& t_related, bool verbose) {
  std::vector<std::pair<size_t,size_t> > lcs_xs = LCS(X,S,verbose);
  std::vector<std::pair<size_t,size_t> > ali_st = ALI(A,verbose);
  std::set<size_t> myset;

  //build s2x
  std::vector<std::set<size_t> > s2x(S.size(),myset); //fill of empty sets
  for (size_t i = 0; i < lcs_xs.size(); i++) {
    s2x[lcs_xs[i].second].insert(lcs_xs[i].first);
  }
  //build t2s
  std::vector<std::set<size_t> > t2s(T.size(),myset); //fill of empty sets
  for (size_t i = 0; i < ali_st.size(); i++) {
    t2s[ali_st[i].second].insert(ali_st[i].first);
  }

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


void usage(std::string name){
  std::cerr << "usage: " << name << " -o FILE -s FILE -t FILE -a FILE -tst FILE -match FILE [-col INT] [-sep STRING] [-v]" << std::endl;
  std::cerr << "   -o      FILE : output file" << std::endl;
  std::cerr << "   -s      FILE : train src file" << std::endl;
  std::cerr << "   -t      FILE : train tgt file" << std::endl;
  std::cerr << "   -a      FILE : train ali file" << std::endl;
  std::cerr << "   -tst    FILE : test source file" << std::endl;
  std::cerr << "   -match  FILE : test match file" << std::endl;
  std::cerr << "   -col     INT : column where match index is found (default 0)" << std::endl;
  std::cerr << "   -embedding   : do not perform alignments" << std::endl;
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
  std::cerr << "C: source words with related target (to copy some target word)" << std::endl;
  std::cerr << "T: target words with related source (within the match)" << std::endl;
  std::cerr << "U: target words without related source (without the match)" << std::endl;
  std::cerr << "E: target words from similar sentence using embeddings (no alignments performed)" << std::endl;
  std::cerr << std::endl;
  std::cerr << "Comments:" << std::endl;
  std::cerr << "All files are lightly tokenised (split punctuation)" << std::endl;

  return;
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
  std::string sepwords = " ";
  std::string sepsents = "‖";
  bool embedding = false;
  std::string tagS = "S";
  std::string tagC = "C";
  std::string tagT = "T";
  std::string tagU = "U";
  std::string tagE = "E";
  size_t col = 0;
  for (size_t i = 1; i < argc; i++){
    std::string tok = argv[i];
    if (tok == "-s" and i<argc) { i++; fsrc = argv[i]; }
    else if (tok == "-t" and i<argc) { i++; ftgt = argv[i]; }
    else if (tok == "-a" and i<argc) { i++; fali = argv[i]; }
    else if (tok == "-tst" and i<argc) { i++; ftst = argv[i]; }
    else if (tok == "-match" and i<argc) { i++; fmatch = argv[i]; }
    else if (tok == "-col" and i<argc) { i++; col = std::atoi(argv[i]); }
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
    if (cols.size() < col+1){
      if (verbose) std::cout << "no match" << std::endl;
    }
    /*** there is a match ********************/
    else {
      size_t j = std::atoi(cols[col].c_str()) - 1;
      if (j >= vsrc.size()){
	std::cerr << "error: match out of bounds!" << std::endl;
	return 1;
      }
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
    }
    //write senetnces in corresponding files
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
