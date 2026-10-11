#include <stdio.h>
#include <stdlib.h>
#include "xgb_model.h"

int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "usage: harness features.csv n_features\n"); return 1; }
    FILE *f = fopen(argv[1], "r");
    int n = atoi(argv[2]);
    if (!f || n != XGB_N_FEATURES) { fprintf(stderr, "bad input\n"); return 1; }
    float raw[XGB_N_FEATURES];
    for (;;) {
        for (int i = 0; i < n; i++) {
            if (fscanf(f, i ? ",%f" : "%f", &raw[i]) != 1) { fclose(f); return 0; }
        }
        printf("%d\n", xgb_predict_raw(raw));
    }
}
