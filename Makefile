train_STEP1:
	bash FineTune/bashfile/quick_train_with_struct_data.sh
train_STEP2:
	bash FineTune/bashfile/quick_train_with_highqual_data.sh
train_STEP3:
	bash FineTune/bashfile/quick_train_with_highqual_weightedloss.sh