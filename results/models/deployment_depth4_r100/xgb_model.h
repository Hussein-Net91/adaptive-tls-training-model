#ifndef XGB_MODEL_H
#define XGB_MODEL_H
#ifdef __cplusplus
extern "C" {
#endif
/* XGBoost 300 trees = 100 rounds x 3 classes; 0=Good 1=Medium 2=Bad */
/* feature order: lat_per_byte, E_lat_per_byte, cycles_per_bit, throughput, Energy, stack_per_msg, latency, E_latency, cycles_mean, payload_size, heap_per_msg, Flash_used, Ex_code, rodata, total_memory, cv_latency, lat_per_byte_std, E_lat_per_byte_std */
#define XGB_N_CLASSES 3
#define XGB_N_FEATURES 18
void xgb_scale_features(const float*,float*);
int xgb_predict(const float*);
int xgb_predict_raw(const float*);
const char *xgb_class_label(int);
#ifdef __cplusplus
}
#endif
#endif
