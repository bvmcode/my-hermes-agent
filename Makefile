# INSTANCE_ID is the EC2 instance id. An exported value wins. Otherwise Make
# reads it from infra/outputs.txt, which terraform apply writes.
INSTANCE_ID ?= $(shell sed -n 's/^export INSTANCE_ID=//p' infra/outputs.txt)

ifeq ($(strip $(INSTANCE_ID)),)
$(error INSTANCE_ID is unset. Run terraform apply, or export INSTANCE_ID)
endif

export INSTANCE_ID

AWS_REGION := $(shell sed -n "s/^export connect_ssm='aws ssm start-session --region \([^ ]*\).*/\1/p" infra/outputs.txt)
ifeq ($(strip $(AWS_REGION)),)
AWS_REGION := us-east-1
endif

.PHONY: login dashboard-login

login:
	aws ssm start-session --region $(AWS_REGION) --target $(INSTANCE_ID) \
		--document-name AWS-StartInteractiveCommand \
		--parameters command="sudo -iu ubuntu"

dashboard-login:
	cmd_id=$$(aws ssm send-command --region $(AWS_REGION) --instance-ids $(INSTANCE_ID) \
		--document-name AWS-RunShellScript --query Command.CommandId --output text \
		--parameters 'commands=["sudo grep -E \"^HERMES_DASHBOARD_BASIC_AUTH_(USERNAME|PASSWORD)=\" /home/ubuntu/.hermes/.env"]'); \
	status=; \
	i=0; \
	while [ $$i -lt 15 ]; do \
		status=$$(aws ssm get-command-invocation --region $(AWS_REGION) --command-id $$cmd_id \
			--instance-id $(INSTANCE_ID) --query Status --output text 2>/dev/null || true); \
		case $$status in Success|Failed|Cancelled|TimedOut) break;; esac; \
		i=$$((i + 1)); \
		sleep 2; \
	done; \
	aws ssm get-command-invocation --region $(AWS_REGION) --command-id $$cmd_id \
		--instance-id $(INSTANCE_ID) --query StandardOutputContent --output text; \
	test "$$status" = Success
