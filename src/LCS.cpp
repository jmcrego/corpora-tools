#include <iostream>
#include <vector>
#include <set>
#include "LCS.h"

LCS::LCS(std::vector<std::string> X, std::vector<std::string> Y){
  size_t x = X.size();
  size_t y = Y.size();
  std::set<size_t> myset;
  for (size_t i=0; i<x; i++) x2y.push_back(myset);
  for (size_t i=0; i<y; i++) y2x.push_back(myset);
  size_t L[x+1][y+1];
  //find lcs
  for (int i=0; i<=x; i++) {
    for (int j=0; j<=y; j++) {
      if (i == 0 || j == 0) L[i][j] = 0;
      else if (X[i-1] == Y[j-1]) L[i][j] = L[i-1][j-1] + 1;
      else L[i][j] = std::max(L[i-1][j], L[i][j-1]);
    }
  }
  // Start from the right-most-bottom-most corner to recover lcs
  while (x > 0 && y > 0) {
    // if same, part of the result
    if (X[x-1] == Y[y-1]) {
      lcs_xy.insert(lcs_xy.begin(),std::make_pair(x-1,y-1));
      lcs.insert(lcs.begin(),X[x-1]);
      x2y[x-1].insert(y-1);
      y2x[y-1].insert(x-1);
      x--;
      y--;
    }
    // If not same, then find the larger of two and go in the direction of larger value
    else if (L[x-1][y] > L[x][y-1]) x--;
    else y--;
  }
  return;
}

