class Align{

public:
  size_t len_x;
  size_t len_y;
  bool consecutive;
  std::vector<std::set<size_t> > x2y;
  std::vector<std::set<size_t> > y2x;
  std::vector<std::pair<size_t,size_t> > ali_xy;
  Align(std::vector<std::string> A,size_t,size_t);
  std::set<std::pair<std::set<size_t>, std::set<size_t> > > Groups_src(bool);
  void aligned_to_s(std::set<size_t>&, std::set<size_t>&);
  std::set<std::pair<std::set<size_t>, std::set<size_t> > > Groups_tgt(bool);
  void aligned_to_t(std::set<size_t>&, std::set<size_t>&);
};
