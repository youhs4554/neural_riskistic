curl -X POST  "http://localhost:8081/models?url=model_store/STCNet_8f_CesleaFDD6.mar" &&
curl -v -X PUT "http://localhost:8081/models/STCNet_8f_CesleaFDD6?min_worker=3"