from cdktf import App

from Stacks import k8s_stack

# app_vm = App(outdir='vm', stack_traces=False)
app_k8s = App(outdir='k8s', stack_traces=False)
#virtual_machibe_stack.MyVirtualMachine(app_vm, "virtual-machine")
k8s_stack.MyK8S(app_k8s, "k8s-cluster")
app_k8s.synth()
#app_vm.synth()
