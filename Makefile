train_STEP1_CoT:
	FINETUNE_CONFIG=config_CoT.json bash FineTune/bashfile/quick_train_with_struct_data.sh
train_STEP2_CoT:
	FINETUNE_CONFIG=config_CoT.json bash FineTune/bashfile/quick_train_with_highqual_data.sh
train_STEP3_CoT:
	FINETUNE_CONFIG=config_CoT.json bash FineTune/bashfile/quick_train_with_highqual_weightedloss.sh

deploy_STEP2_CoT:
	DEPLOY_CONFIG=Deployment/config_CoT.json bash Deployment/benchmark/bash_script/quick_LoRA_STEP2.sh
deploy_STEP3_CoT:
	DEPLOY_CONFIG=Deployment/config_CoT.json bash Deployment/benchmark/bash_script/quick_LoRA_STEP3.sh

test_STEP2_CoT:
	DEPLOY_CONFIG=config_CoT.json python -m Deployment.benchmark.v1.test_STEP2
test_STEP3_CoT:
	DEPLOY_CONFIG=config_CoT.json python -m Deployment.benchmark.v1.test_STEP3

train_STEP1_NoCoT:
	FINETUNE_CONFIG=config_NoCoT.json bash FineTune/bashfile/quick_train_with_struct_data.sh
train_STEP2_NoCoT:
	FINETUNE_CONFIG=config_NoCoT.json bash FineTune/bashfile/quick_train_with_highqual_data.sh
train_STEP3_NoCoT:
	FINETUNE_CONFIG=config_NoCoT.json bash FineTune/bashfile/quick_train_with_highqual_weightedloss.sh

deploy_STEP2_NoCoT:
	DEPLOY_CONFIG=Deployment/config_NoCoT.json bash Deployment/benchmark/bash_script/quick_LoRA_STEP2.sh
deploy_STEP3_NoCoT:
	DEPLOY_CONFIG=Deployment/config_NoCoT.json bash Deployment/benchmark/bash_script/quick_LoRA_STEP3.sh

test_STEP2_NoCoT:
	DEPLOY_CONFIG=config_NoCoT.json python -m Deployment.benchmark.v1.test_STEP2
test_STEP3_NoCoT:
	DEPLOY_CONFIG=config_NoCoT.json python -m Deployment.benchmark.v1.test_STEP3