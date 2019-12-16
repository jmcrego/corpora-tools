class Align{

public:
  size_t len_x;
  size_t len_y;
  std::vector<std::set<size_t> > x2y;
  std::vector<std::set<size_t> > y2x;
  std::vector<std::pair<size_t,size_t> > ali_xy;
  Align(std::vector<std::string> A,size_t,size_t);
  std::vector<std::pair<std::set<size_t>, std::set<size_t> > > Group(bool);
};

