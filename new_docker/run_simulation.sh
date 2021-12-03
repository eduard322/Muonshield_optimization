#!/bin/bash
#if [ -z "$AZURE_INPUT_DATA_URI" ]
#then
#    echo "AZURE_DATA_URI is given. Starting downloading data from $AZURE_INPUT_DATA_URI..."
#    azcopy cp "$AZURE_INPUT_DATA_URI" "/sample" --recursive
#fi
alienv -w /sw setenv  FairShip/latest  -c /bin/bash  -c "python run_opt.py --FastMuon --processMiniShield  --MuonBack -f muon_input/reweighted_input_test.root --optParams \"$PARAMS\" --nEvents $nEvents --firstEvent $first_event --output shield_files/outputs/   --muShieldDesign 8 -g /ship/shield_files/geometry/shield_params.root"
# alienv -w /sw setenv  FairShip/latest  -c /bin/bash  -c "python process_run.py"
if [ ! -z "$AZURE_OUTPUT_DATA_URI" ]
then
    echo "Starting uploading results to $AZURE_OUTPUT_DATA_URI..."
    azcopy cp "/ship/shield_files/outputs/*" "$AZURE_OUTPUT_DATA_URI" --recursive
else
    echo "AZURE_OUTPUT_DATA_URI wasn't given given"
fi
#cp shield_files/outputs/ship.conical.MuonBack-TGeant4.root .
#cp
