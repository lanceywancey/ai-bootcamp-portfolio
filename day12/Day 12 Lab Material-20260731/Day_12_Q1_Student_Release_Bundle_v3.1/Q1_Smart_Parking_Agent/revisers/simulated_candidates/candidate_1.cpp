#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <string>
struct Input { int parking_minutes; std::string vehicle_type; int import_wh; int import_rate_cents_per_kwh; int export_wh; int export_rate_cents_per_kwh; bool vehicle_v2g; bool station_v2g; bool owner_opt_in; int soc_after_export; int minimum_departure_soc; };
struct Result { int parking_fee_cents; int import_cost_cents; int export_credit_cents; int net_amount_cents; };
void validate(const Input& i) {
    if (i.parking_minutes < 0 || i.parking_minutes > 1440) throw std::invalid_argument("invalid parking_minutes");
    if (i.vehicle_type != "ICE_CAR" && i.vehicle_type != "EV_CAR" && i.vehicle_type != "MOTORCYCLE") throw std::invalid_argument("invalid vehicle_type");
    if (i.import_wh < 0 || i.export_wh < 0 || i.import_rate_cents_per_kwh < 0 || i.export_rate_cents_per_kwh < 0) throw std::invalid_argument("negative energy or tariff");
    if (i.export_wh > 0 && (i.vehicle_type != "EV_CAR" || !i.vehicle_v2g || !i.station_v2g || !i.owner_opt_in)) throw std::invalid_argument("V2G export not permitted");
}
int calculate_parking_fee(const Input& i) {
    if (i.parking_minutes <= 15) return 0;
    const int hours = (i.parking_minutes + 59) / 60;
    if (i.vehicle_type == "MOTORCYCLE") return std::min(100 + (hours - 1) * 75, 1000);
    return std::min(200 + (hours - 1) * 150, 2000);
}
int calculate_energy_amount(int wh, int rate) { return (wh * rate + 500) / 1000; }
Result calculate_settlement(const Input& i) {
    const int parking = calculate_parking_fee(i);
    const int imported = calculate_energy_amount(i.import_wh, i.import_rate_cents_per_kwh);
    const int exported = calculate_energy_amount(i.export_wh, i.export_rate_cents_per_kwh);
    return {parking, imported, exported, parking + imported - exported};
}
Input parse_arguments(int argc, char* argv[]) { if (argc != 12) throw std::invalid_argument("expected 11 arguments"); return {std::stoi(argv[1]),argv[2],std::stoi(argv[3]),std::stoi(argv[4]),std::stoi(argv[5]),std::stoi(argv[6]),std::stoi(argv[7])!=0,std::stoi(argv[8])!=0,std::stoi(argv[9])!=0,std::stoi(argv[10]),std::stoi(argv[11])}; }
int main(int argc,char* argv[]){try{auto i=parse_arguments(argc,argv);validate(i);auto r=calculate_settlement(i);std::string s=r.net_amount_cents<0?"CREDIT":(r.net_amount_cents>0?"PAY":"ZERO");std::cout<<"{\"status\":\"ok\",\"parking_fee_cents\":"<<r.parking_fee_cents<<",\"import_cost_cents\":"<<r.import_cost_cents<<",\"export_credit_cents\":"<<r.export_credit_cents<<",\"net_amount_cents\":"<<r.net_amount_cents<<",\"settlement\":\""<<s<<"\"}\n";return 0;}catch(const std::exception&e){std::cout<<"{\"status\":\"error\",\"error\":\""<<e.what()<<"\"}\n";return 2;}}
