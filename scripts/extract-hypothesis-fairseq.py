# -*- encoding: utf-8 -*-
import argparse
import os
import io
from collections import defaultdict

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-o', type=str, default="output.txt", help='FairSeq Output file')
    parser.add_argument('-f', type=str, default="final-hypothesis.txt", help='FairSeq Final Hypothesis File')
    args = parser.parse_args()

    f_output_data = io.open(args.o, encoding="utf-8").readlines()    

    hyp_dict = {}
    hypos_dict = defaultdict(list)
    for line in f_output_data:
        if line.startswith("H-"):
            words = line.split()
            sentid = int(words[0].split("-")[1])
            hyp = " ".join(words[2:])
            hyp_dict[sentid] = hyp
            hypos_dict[sentid].append(hyp)
    print(len(hyp_dict))

    sentids = list(hyp_dict.keys())
    sentids.sort()
    
    with io.open(args.f, "w", encoding="utf-8") as f_hyp:
        for sentid in sentids:
            # f_hyp.write(hyp_dict[sentid]+"\n")
            assert len(hypos_dict[sentid]) == 10
            for hyp in hypos_dict[sentid]:
                f_hyp.write(hyp+'\n')
            
