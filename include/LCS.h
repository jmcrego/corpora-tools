class LCS{

public:
  std::vector<std::set<size_t> > x2y;
  std::vector<std::set<size_t> > y2x;
  std::vector<std::pair<size_t,size_t> > lcs_xy;
  std::vector<std::string> lcs;

  LCS(std::vector<std::string> X, std::vector<std::string>);
};

