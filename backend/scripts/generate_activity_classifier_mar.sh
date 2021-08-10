# when new check point version comes up, update this!
zip -r activity_lib.zip activity_lib && \
torch-model-archiver --model-name STCNet_8f_CesleaFDD6 \
--force \
--version 1.0 \
--serialized-file model_ckpt/STCNet_8f_CesleaFDD6-1/version_2/checkpoints/epoch\=45.ckpt \
--export-path model_store \
--handler handlers/activity_classifier.py \
--extra-files activity_lib.zip,model_ckpt/STCNet_8f_CesleaFDD6-1/version_2/hparams.yaml,handlers/handler_utils.py