// New Section 30 campaign. Numerical log traversal, not interval certification.
// Standard-library implementation; no fast-math and no external C++ packages.
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <sys/resource.h>
#include <vector>

using I = __int128_t;
using Clock = std::chrono::steady_clock;
constexpr I SCALE = (I(1) << 53) * 15625; // 2^53 * 5^6
constexpr I EPS = I(1) << 47;           // SCALE / 10^6
constexpr double RADIUS = 1e-6;
void require(bool ok, const std::string& why) { if (!ok) throw std::runtime_error(why); }
double seconds(Clock::time_point t) { return std::chrono::duration<double>(Clock::now()-t).count(); }
std::string integer(I n) {
    if (!n) return "0";
    bool neg=n<0; if (neg) n=-n;
    std::string s; while(n) { s.push_back(char('0'+n%10)); n/=10; }
    if(neg) s.push_back('-'); std::reverse(s.begin(),s.end()); return s;
}
I checked_mul(I a,I b) {
    I v; require(!__builtin_mul_overflow(a,b,&v),"signed 128-bit product overflow"); return v;
}
I gcd128(I a,I b) { while(b) { I t=a%b;a=b;b=t; }return a; }
std::string fraction(I a,I b) {
    require(a>=0 && b>0,"invalid nonnegative fraction"); I g=gcd128(a,b);a/=g;b/=g;
    return integer(a)+(b==1?"":"/"+integer(b));
}
I scaled(double x) {
    require(std::isfinite(x) && x>=0.5 && x<=8193,"exact scaling needs x in [0.5,8193]");
    uint64_t bits; std::memcpy(&bits,&x,8);
    int exponent=int((bits>>52)&2047)-1023;
    uint64_t mantissa=(bits&((uint64_t(1)<<52)-1))|(uint64_t(1)<<52);
    require(exponent>=-1 && exponent<=13,"unexpected binary64 exponent");
    I result=checked_mul(I(mantissa),15625) << (exponent+1);
    require(result>0 && result<(I(1)<<81),"endpoint numerator range exceeded");
    return result;
}
std::string quote(const std::string& s) {
    std::string out="\"";
    for(char c:s) { if(c=='"'||c=='\\')out+='\\'; require(c>=32,"unexpected control character");out+=c; }
    return out+'"';
}
std::string number(double x) {std::ostringstream o;o<<std::setprecision(17)<<x;return o.str();}
struct File {
    FILE* f=nullptr;
    explicit File(const std::string& path) {
        f=std::fopen(path.c_str(),"wbx"); require(f,"output already exists or cannot be created: "+path);
        std::setvbuf(f,nullptr,_IOFBF,1<<20);
    }
    void bytes(const void* p,size_t n) { require(std::fwrite(p,1,n,f)==n,"output write failure"); }
    void close() { if(f) { FILE* old=f;f=nullptr;require(std::fclose(old)==0,"output close failure"); } }
    ~File(){if(f)std::fclose(f);}
};
struct Slope { int32_t p,q; bool operator<(const Slope& b) const {return std::tie(p,q)<std::tie(b.p,b.q);} };
struct Curve { Slope s; double length; int sector,depth; };
std::string curve_json(const Curve& c) {
    std::ostringstream o;o<<std::setprecision(17)<<"{\"slope\":["<<c.s.p<<','<<c.s.q
        <<"],\"length_binary64\":"<<c.length<<",\"sector\":"<<c.sector<<",\"depth\":"<<c.depth<<'}';return o.str();
}
std::string maybe_curve(bool found,const Curve& c) {return found?curve_json(c):"null";}
struct Nearest {
    double cutoff; bool below=false,above=false; Curve lo{},hi{};
    void add(const Curve& c) {
        if(c.length<=cutoff && (!below || c.length>lo.length || (c.length==lo.length && c.s<lo.s))) {lo=c;below=true;}
        if(c.length>cutoff && (!above || c.length<hi.length || (c.length==hi.length && c.s<hi.s))) {hi=c;above=true;}
    }
};
struct Stats {
    uint64_t included=0,visited=0,pruned=0,hash=14695981039346656037ULL;
    std::array<uint64_t,3> sectors{0,0,0};
    std::array<Curve,3> deepest{};
    double max_ratio=0,min_growth=std::numeric_limits<double>::infinity();
    int max_coordinate=0,max_depth=0;
    void identity(Slope s) {
        // Explicit little-endian FNV-1a64 stream, roots then sectors 0,1,2,
        // depth-first with the left child first. SHA256 of the sidecar is
        // computed separately by the orchestrating Python driver.
        for(int32_t v:{s.p,s.q}) for(int j=0;j<4;++j) {hash^=(uint32_t(v)>>(8*j))&255;hash*=1099511628211ULL;}
    }
};
struct Node { Slope left,right; double a,b,opposite; int depth; };
double length_from_log(double u) {
    require(std::isfinite(u)&&u>std::log(2.0),"nonfinite or nonhyperbolic log trace");
    double r=4*std::exp(-2*u);require(r>=0&&r<1,"length square-root domain failure");
    double ell=2*(u+std::log1p((std::sqrt(1-r)-1)/2));
    require(std::isfinite(ell)&&ell>0,"invalid length");return ell;
}
Slope mediant(Slope a,Slope b) {
    I det=I(a.p)*b.q-I(a.q)*b.p; require(det==1||det==-1,"Farey determinant is not unimodular");
    int64_t p=int64_t(a.p)+b.p,q=int64_t(a.q)+b.q;
    require(p>INT32_MIN&&p<=INT32_MAX&&q>INT32_MIN&&q<=INT32_MAX,"slope addition overflow");
    return {int32_t(p),int32_t(q)};
}
Slope canonical(Slope s) {if(s.q<0||(s.q==0&&s.p<0)) {s.p=-s.p;s.q=-s.q;}return s;}
template<class Visitor> Stats enumerate(const std::array<double,3>& roots,double guard,Visitor visit) {
    for(double r:roots)require(std::isfinite(r)&&r>2,"finite root traces >2 required");
    double x=roots[0],y=roots[1],z=roots[2];
    require(x<=y&&y<=z&&2*z<=x*y,"root is not reduced");
    require(std::abs(x*x+y*y+z*z-x*y*z)<1e-11,"root Markoff residual failed");
    require(std::isfinite(guard)&&guard>=4&&guard<=8192+2e-6,"invalid enumeration cutoff");
    std::array<double,3> u{std::log(x),std::log(y),std::log(z)};
    Stats stats;
    auto accept=[&](Curve c,bool included) {
        stats.max_coordinate=std::max({stats.max_coordinate,std::abs(c.s.p),c.s.q});
        if(included) { ++stats.included;stats.identity(c.s); if(c.sector>=0) {
            ++stats.sectors[c.sector];stats.max_depth=std::max(stats.max_depth,c.depth);
            auto& d=stats.deepest[c.sector];if(c.depth>d.depth || (c.depth==d.depth&&c.s<d.s)) d=c;
        }}
        visit(c,included);
    };
    accept({{1,0},length_from_log(u[0]),-1,0},true);
    accept({{0,1},length_from_log(u[1]),-1,0},true);
    accept({{1,1},length_from_log(u[2]),-1,0},true);
    std::array<Node,3> initial{{{{1,0},{0,-1},u[0],u[1],u[2],1},
                               {{1,0},{1,1},u[0],u[2],u[1],1},
                               {{0,1},{1,1},u[1],u[2],u[0],1}}};
    for(int sector=0;sector<3;++sector) {
        std::vector<Node> stack{initial[sector]};
        while(!stack.empty()) {
            Node n=stack.back();stack.pop_back();++stats.visited;
            Slope raw=mediant(n.left,n.right);
            double ratio=std::exp(n.opposite-n.a-n.b);
            require(std::isfinite(ratio)&&ratio>=0&&ratio<=0.5+1e-15,"outward subtraction ratio failure");
            double c=n.a+n.b+std::log1p(-ratio);
            double growth=c-std::max(n.a,n.b);require(std::isfinite(c)&&growth>0,"outward trace is not increasing");
            stats.max_ratio=std::max(stats.max_ratio,ratio);stats.min_growth=std::min(stats.min_growth,growth);
            Curve curve{canonical(raw),length_from_log(c),sector,n.depth};
            bool included=curve.length<=guard;accept(curve,included);
            if(!included) {++stats.pruned;continue;}
            require(n.depth<INT32_MAX,"depth overflow");
            stack.push_back({raw,n.right,c,n.b,n.a,n.depth+1});
            stack.push_back({n.left,raw,n.a,c,n.b,n.depth+1});
        }
    }
    require(stats.included< (uint64_t(1)<<26),"count exceeds exact sensitivity arithmetic contract");
    require(stats.visited==2*(stats.included-3)+3&&stats.pruned==stats.included,"binary-tree accounting failed");
    return stats;
}
struct Maximum {
    int64_t absolute=0,d=0; I position=1; double x=0;std::string side="initial_value";
    void consider(int64_t value,I at,double location,const std::string& which) {
        int64_t a=std::abs(value);require(a<(int64_t(1)<<29),"D arithmetic range exceeded");
        if(checked_mul(a,position)>checked_mul(absolute,at)) {absolute=a;d=value;position=at;x=location;side=which;}
    }
    std::string json() const {
        std::ostringstream o;o<<std::setprecision(17)<<"{\"value\":"<<double(absolute)*double(SCALE)/double(position)
        <<",\"exact_rational_for_stored_events\":"<<quote(fraction(checked_mul(absolute,SCALE),position))
        <<",\"position_binary64\":"<<x<<",\"position_scaled_integer\":"<<quote(integer(position))
        <<",\"side\":"<<quote(side)<<",\"D\":"<<d<<'}';return o.str();
    }
};
struct Kahan {double sum=0,correction=0;void add(double x){double y=x-correction,t=sum+y;correction=(t-sum)-y;sum=t;}};
struct Block {
    int T;Maximum maximum;double q;uint64_t events,checks;double direct_d_residual;
    std::string json() const {
        std::ostringstream o;o<<std::setprecision(17)<<"{\"T\":"<<T<<",\"M\":"<<maximum.json()
          <<",\"Q\":"<<q<<",\"Q_squared\":"<<q*q<<",\"event_positions_in_block\":"<<events
          <<",\"independent_direct_count_checks\":"<<checks<<",\"maximum_integer_D_residual\":"<<direct_d_residual<<'}';return o.str();
    }
};
int64_t count_at(const std::vector<double>& lengths,double t,bool left) {
    return (left?std::lower_bound(lengths.begin(),lengths.end(),t):std::upper_bound(lengths.begin(),lengths.end(),t))-lengths.begin();
}
int64_t all_point_count(const std::vector<double>& lengths,int L) {
    I threshold=scaled(L);int64_t result=0;
    int64_t multiples=int64_t(threshold/scaled(lengths.front()));
    for(int64_t k=1;k<=multiples;++k) {
        size_t lo=0,hi=lengths.size();
        while(lo<hi){size_t mid=lo+(hi-lo)/2;if(checked_mul(k,scaled(lengths[mid]))<=threshold)lo=mid+1;else hi=mid;}
        require(lo<size_t(INT64_MAX/2-result),"all-point count overflow");result+=2*int64_t(lo);
    }
    if(L<=64) {
        int64_t direct=0;for(double ell:lengths){if(ell>L)break;direct+=2*int64_t(threshold/scaled(ell));}
        require(direct==result,"all-point direct floor sum mismatch");
    }
    return result;
}
Block metrics(const std::vector<double>& lengths,int T,bool every_interval) {
    require(T>=1&&T<=2048,"block start outside supported range");
    double end=2.0*T,prev=T;int64_t f=count_at(lengths,T,false),h=count_at(lengths,2*T,false),d=h-4*f;
    Maximum best;best.position=scaled(T);best.x=T;best.consider(d,scaled(T),T,"initial_value");Kahan integral;uint64_t events=0,checks=0;
    auto direct=[&](double at,bool left,int64_t expected){int64_t actual=count_at(lengths,2*at,left)-4*count_at(lengths,at,left);require(actual==expected,"direct D count mismatch");++checks;};
    direct(T,false,d);
    while(true) {
        double a=f<int64_t(lengths.size())?lengths[f]:INFINITY;
        double b=h<int64_t(lengths.size())?lengths[h]/2:INFINITY;
        double at=std::min(a,b);if(at>end)break;
        require(at>prev,"event sweep failed strict ordering");
        integral.add(double(d)*double(d)*((at-prev)/(prev*at)));
        if(every_interval||events%100003==0) {
            direct(at,true,d);
            // Count on an interior representable point, or at the previous
            // endpoint when no representable midpoint exists.
            double mid=prev+(at-prev)/2;direct((mid>prev&&mid<at)?mid:prev,false,d);
        }
        best.consider(d,scaled(at),at,"left_limit");
        while(f<int64_t(lengths.size())&&lengths[f]==at)++f;
        while(h<int64_t(lengths.size())&&lengths[h]/2==at)++h;
        d=h-4*f;best.consider(d,scaled(at),at,"value_after_group");
        if(every_interval||events%100003==0)direct(at,false,d);
        prev=at;++events;
    }
    integral.add(double(d)*double(d)*((end-prev)/(prev*end)));
    best.consider(d,scaled(end),end,"terminal_value");direct(end,false,d);
    if(best.side=="left_limit")direct(best.x,true,best.d);else direct(best.x,false,best.d);
    require(std::isfinite(integral.sum)&&integral.sum>=0,"invalid Q integral");
    return {T,best,std::sqrt(integral.sum/T),events,checks,0};
}
struct Bound {int64_t numerator=0;I denominator=1;std::string side="initial_value";
    void consider(int64_t n,I p,const std::string& s){require(n>=0&&n<(int64_t(1)<<29),"sensitivity D range exceeded");
        if(checked_mul(n,denominator)>checked_mul(numerator,p)) {numerator=n;denominator=p;side=s;}}
    std::string exact()const{return fraction(checked_mul(numerator,SCALE),denominator);}
    double value()const{return double(numerator)*double(SCALE)/double(denominator);}
};
struct Envelope {int T;Bound lower,upper;uint64_t events;
    std::string json()const{std::ostringstream o;o<<std::setprecision(17)<<"{\"T\":"<<T
       <<",\"lower_exact_rational\":"<<quote(lower.exact())<<",\"upper_exact_rational\":"<<quote(upper.exact())
       <<",\"lower_approx\":"<<lower.value()<<",\"upper_approx\":"<<upper.value()
       <<",\"width_display_approx\":"<<upper.value()-lower.value()<<",\"endpoint_groups\":"<<events
       <<",\"lower_maximizer_scaled_position\":"<<quote(integer(lower.denominator))
       <<",\"upper_maximizer_scaled_position\":"<<quote(integer(upper.denominator))<<'}';return o.str();}
};
Envelope sensitivity(const std::vector<double>& lengths,int T,I epsilon=EPS) {
    require(lengths.size()<(uint64_t(1)<<26),"sensitivity count range exceeded");
    require(epsilon==0||epsilon==EPS,"unsupported rational epsilon");
    // Streams: full lower, full upper, half lower, half upper.
    auto endpoint=[&](size_t i,int stream)->I {
        if(i==lengths.size())return I(1)<<100;
        I n=scaled(lengths[i])+(stream%2?epsilon:-epsilon);
        require(n>0&&n<(I(1)<<81),"sensitivity endpoint range exceeded");
        if(stream>=2) {require(n%2==0,"common denominator does not represent half endpoint");n/=2;}return n;
    };
    I begin=scaled(T),end=scaled(2*T);std::array<size_t,4> at{};
    for(int s=0;s<4;++s){size_t lo=0,hi=lengths.size();while(lo<hi){size_t mid=lo+(hi-lo)/2;if(endpoint(mid,s)<=begin)lo=mid+1;else hi=mid;}at[s]=lo;}
    Bound low,high;uint64_t events=0;
    auto evaluate=[&](I p,const std::string& side){
        int64_t dlo=int64_t(at[3])-4*int64_t(at[0]),dhi=int64_t(at[2])-4*int64_t(at[1]);
        require(dlo<=dhi,"D envelope is inverted");
        int64_t a=(dlo<=0&&dhi>=0)?0:std::min(std::abs(dlo),std::abs(dhi));
        low.consider(a,p,side);high.consider(std::max(std::abs(dlo),std::abs(dhi)),p,side);
    };
    evaluate(begin,"initial_value");I prev=begin;
    std::array<I,4> next;for(int s=0;s<4;++s)next[s]=endpoint(at[s],s);
    while(true){I p=*std::min_element(next.begin(),next.end());if(p>end)break;
        require(p>prev,"sensitivity endpoint ordering failed");evaluate(p,"left_limit");
        for(int s=0;s<4;++s)while(next[s]==p){++at[s];next[s]=endpoint(at[s],s);}
        evaluate(p,"value_after_group");prev=p;++events;
    }
    evaluate(end,"terminal_value");require(checked_mul(low.numerator,high.denominator)<=checked_mul(high.numerator,low.denominator),"M envelope inverted");
    return {T,low,high,events};
}
std::set<Slope> alternating_targets() {
    std::set<Slope> out;
    for(int sector=0;sector<3;++sector)for(int orientation=0;orientation<2;++orientation) {
        Slope a=sector==2?Slope{0,1}:Slope{1,0};
        Slope b=sector==0?Slope{0,-1}:Slope{1,1};
        for(int depth=1;depth<=16;++depth){Slope c=mediant(a,b);if(depth==6||depth==10||depth==14||depth==16)out.insert(canonical(c));
            if((depth+orientation)%2)a=c;else b=c;}
    }
    return out;
}
bool twist_target(const Curve& c) {
    if(c.sector<0)return false;int a,b;
    if(c.sector==0){a=-c.s.p;b=c.s.q;}else if(c.sector==1){a=c.s.p-c.s.q;b=c.s.q;}else{a=c.s.q-c.s.p;b=c.s.p;}
    return std::min(a,b)==1&&(c.depth==16||c.depth==64||c.depth==256||c.depth==1024||c.depth==2048||c.depth==4096);
}
void write_text(const std::string& path,const std::string& text){File f(path);f.bytes(text.data(),text.size());f.close();}
void validate_lengths(const std::vector<double>& lengths){for(double x:lengths)require(std::isfinite(x)&&x>=1&&x<=8193,"length list must be finite and in [1,8193]");}
int main(int argc,char** argv) {try {
    require(sizeof(double)==8&&std::numeric_limits<double>::is_iec559&&std::numeric_limits<double>::digits==53,"binary64 required");
    uint16_t endian=1;require(*reinterpret_cast<unsigned char*>(&endian)==1,"little-endian host required");
    require(argc>=2,"expected campaign or metrics subcommand");std::string mode=argv[1];
    if(mode=="metrics") {
        require(argc==7,"metrics LENGTHS T OUTPUT EPSILON(0|1e-6) DIRECT(0|1)");
        std::ifstream in(argv[2]);require(bool(in),"cannot open lengths file");std::vector<double> lengths;std::string token;
        while(in>>token)lengths.push_back(std::stod(token));validate_lengths(lengths);std::sort(lengths.begin(),lengths.end());
        int T=std::stoi(argv[3]);I epsilon=std::string(argv[5])=="0"?0:EPS;
        require(std::string(argv[5])=="0"||std::string(argv[5])=="1e-6","unsupported epsilon");
        auto block=metrics(lengths,T,std::string(argv[6])=="1");auto bounds=sensitivity(lengths,T,epsilon);
        write_text(argv[4],"{\"block\":"+block.json()+",\"sensitivity\":"+bounds.json()+"}\n");return 0;
    }
    require(mode=="campaign"&&argc==9,"campaign SURFACE CUTOFF PREFIX X Y Z RECORD_LENGTHS(0|1)");
    std::string surface=argv[2],prefix=argv[4];int cutoff=std::stoi(argv[3]);
    require(cutoff>=16&&cutoff<=8192&&(cutoff&(cutoff-1))==0,"cutoff must be dyadic, 16..8192");
    std::array<double,3> roots{std::stod(argv[5]),std::stod(argv[6]),std::stod(argv[7])};
    bool record_lengths=std::string(argv[8])=="1";Clock::time_point total=Clock::now(),stage=total;
    File identities(prefix+".slopes.i32le");File* records=record_lengths?new File(prefix+".curves.i32-i32-f64le"):nullptr;
    std::vector<double> lengths;lengths.reserve(size_t(0.29*(cutoff+1)*(cutoff+1)));
    std::map<Slope,Curve> samples;std::map<Slope,std::set<std::string>> reasons;
    // Declared before replay: twelve distinct closest-below-final-cutoff
    // curves per sector. Equal lengths are resolved by ascending slope.
    // This supplements the twists, alternations, depth and maximizer samples.
    std::array<std::vector<Curve>,3> near_final;
    auto nearer_order=[](const Curve& a,const Curve& b) {
        return a.length<b.length||(a.length==b.length&&b.s<a.s);
    };
    std::vector<Curve> small;auto alternating=alternating_targets();std::vector<Nearest> nearest;
    double guard=std::nextafter(cutoff+RADIUS,INFINITY);
    for(int t=4;t<=cutoff;t*=2)nearest.push_back({double(t)});nearest.push_back({guard});
    auto sample=[&](const Curve& c,const std::string& why){samples[c.s]=c;reasons[c.s].insert(why);};
    auto collect=[&](const Curve& c,bool included){
        for(auto& n:nearest)n.add(c);
        if(!included)return;
        require(c.length>=1&&c.length<=8193,"length outside exact scaling contract");
        lengths.push_back(c.length);identities.bytes(&c.s.p,4);identities.bytes(&c.s.q,4);
        if(records){records->bytes(&c.s.p,4);records->bytes(&c.s.q,4);records->bytes(&c.length,8);}
        if(c.length<=64)small.push_back(c);
        if(twist_target(c))sample(c,"declared_twist_depth");
        if(alternating.count(c.s))sample(c,"declared_alternating_depth");
        if(c.sector>=0&&c.length<=cutoff) {
            auto& selected=near_final[c.sector];
            if(selected.size()<12||nearer_order(selected.front(),c)) {
                if(selected.size()==12)selected.erase(selected.begin());
                selected.insert(std::lower_bound(selected.begin(),selected.end(),c,nearer_order),c);
            }
        }
    };
    Stats stats=enumerate(roots,guard,collect);identities.close();if(records){records->close();delete records;}
    double enumeration_seconds=seconds(stage);stage=Clock::now();std::sort(lengths.begin(),lengths.end());
    double sort_seconds=seconds(stage);stage=Clock::now();
    File stream(prefix+".lengths.f64le");stream.bytes(lengths.data(),lengths.size()*8);stream.close();
    double stream_seconds=seconds(stage);stage=Clock::now();
    std::vector<Block> blocks;std::vector<Envelope> bounds;std::set<double> wanted;
    for(int T=4;T<=cutoff/4;T*=2){blocks.push_back(metrics(lengths,T,cutoff<=64));
        wanted.insert(blocks.back().maximum.x);wanted.insert(2*blocks.back().maximum.x);}
    double metrics_seconds=seconds(stage);stage=Clock::now();
    for(int T=4;T<=cutoff/4;T*=2)bounds.push_back(sensitivity(lengths,T));
    double sensitivity_seconds=seconds(stage);stage=Clock::now();
    std::map<double,int> seen_maximizers;
    Stats replay=enumerate(roots,guard,[&](const Curve& c,bool included){if(included&&wanted.count(c.length)&&seen_maximizers[c.length]++<3)sample(c,"block_maximizer_event");});
    require(replay.included==stats.included&&replay.hash==stats.hash,"second traversal identity mismatch");
    double sample_replay_seconds=seconds(stage);
    for(const auto& c:stats.deepest)sample(c,"maximum_sector_depth");
    for(const auto& sector:near_final)for(const auto& c:sector)sample(c,"declared_twelve_nearest_below_final_cutoff_per_sector");
    for(const auto& n:nearest){if(n.below)sample(n.lo,"nearest_below_cutoff");if(n.above)sample(n.hi,"nearest_above_cutoff_or_pruned_frontier");}
    stage=Clock::now();std::map<int,int64_t> all_points;
    for(int t=4;t<=cutoff;t*=2)all_points[t]=all_point_count(lengths,t);
    double all_point_seconds=seconds(stage);
    struct rusage usage;require(getrusage(RUSAGE_SELF,&usage)==0,"getrusage failed");
    std::ostringstream o;o<<std::setprecision(17)<<"{\"surface\":"<<quote(surface)<<",\"cutoff\":"<<cutoff<<",\"enumeration_guard\":"<<guard
      <<",\"count_through_cutoff\":"<<count_at(lengths,cutoff,false)<<",\"count_through_guard\":"<<lengths.size()
      <<",\"root_count\":3,\"sector_counts\":["<<stats.sectors[0]<<','<<stats.sectors[1]<<','<<stats.sectors[2]<<']'
      <<",\"visited_outward_nodes\":"<<stats.visited<<",\"pruned_frontier_nodes\":"<<stats.pruned
      <<",\"maximum_depth\":"<<stats.max_depth<<",\"maximum_visited_slope_coordinate\":"<<stats.max_coordinate
      <<",\"maximum_subtraction_ratio\":"<<stats.max_ratio<<",\"minimum_outward_log_growth\":"<<stats.min_growth
      <<",\"slope_identity_fnv1a64_decimal\":"<<quote(std::to_string(stats.hash))
      <<",\"double_mantissa_bits\":"<<std::numeric_limits<double>::digits<<",\"long_double_mantissa_bits\":"<<std::numeric_limits<long double>::digits
      <<",\"double_max_exponent\":"<<std::numeric_limits<double>::max_exponent<<",\"long_double_max_exponent\":"<<std::numeric_limits<long double>::max_exponent
      <<",\"exact_endpoint_common_denominator\":"<<quote(integer(SCALE))
      <<",\"raw_peak_rss\":"<<usage.ru_maxrss<<",\"timing_seconds\":{\"enumeration_and_identity_io\":"<<enumeration_seconds
      <<",\"sort\":"<<sort_seconds<<",\"sorted_stream_io\":"<<stream_seconds<<",\"metrics\":"<<metrics_seconds
      <<",\"sensitivity\":"<<sensitivity_seconds<<",\"sample_replay\":"<<sample_replay_seconds
      <<",\"all_point_counts\":"<<all_point_seconds<<",\"native_total\":"<<seconds(total)<<'}';
    o<<",\"counts\":[";bool first=true;
    for(int t=4;t<=cutoff;t*=2){if(!first)o<<',';first=false;o<<"{\"L\":"<<t<<",\"N\":"<<count_at(lengths,t,false)
       <<",\"A_signed_all_point_for_stored_lengths\":"<<all_points[t]
       <<",\"Delta2_A\":"<<(t<=cutoff/2?std::to_string(all_points[2*t]-4*all_points[t]):"null")<<'}';}o<<']';
    o<<",\"cutoff_margins\":[";first=true;for(const auto& n:nearest){if(!first)o<<',';first=false;
       o<<"{\"cutoff\":"<<n.cutoff<<",\"closest_below\":"<<maybe_curve(n.below,n.lo)<<",\"closest_above\":"<<maybe_curve(n.above,n.hi)
       <<",\"below_distance\":"<<(n.below?number(n.cutoff-n.lo.length):"null")
       <<",\"above_distance\":"<<(n.above?number(n.hi.length-n.cutoff):"null")<<'}';}o<<']';
    o<<",\"blocks\":[";first=true;for(const auto& b:blocks){if(!first)o<<',';first=false;o<<b.json();}o<<']';
    o<<",\"conditional_M_bounds\":[";first=true;for(const auto& b:bounds){if(!first)o<<',';first=false;o<<b.json();}o<<']';
    o<<",\"curves_through_64\":[";first=true;for(const auto& c:small){if(!first)o<<',';first=false;o<<curve_json(c);}o<<']';
    o<<",\"selected_curves\":[";first=true;for(const auto& entry:samples){if(!first)o<<',';first=false;auto row=curve_json(entry.second);row.pop_back();o<<row<<",\"selection_reasons\":[";
        bool rfirst=true;for(const auto& why:reasons[entry.first]){if(!rfirst)o<<',';rfirst=false;o<<quote(why);}o<<"]}";}o<<"]}\n";
    write_text(prefix+".native.json",o.str());
    std::cout<<surface<<" cutoff="<<cutoff<<" count="<<count_at(lengths,cutoff,false)<<" native_seconds="<<seconds(total)<<" raw_peak_rss="<<usage.ru_maxrss<<'\n';
    return 0;
}catch(const std::exception& e){std::cerr<<"campaign error: "<<e.what()<<'\n';return 2;}}
