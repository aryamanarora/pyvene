import torch, random
from torch import nn
import numpy as np


lsm = nn.LogSoftmax(dim=2)
sm = nn.Softmax(dim=2)


def get_internal_model_type(model):
    """Return the model type"""
    return type(model)


def is_transformer(model):
    """Determine if this is a transformer model"""
    return True

        
def embed_to_distrib(model, embed, log=False, logits=False):
    """Convert an embedding to a distribution over the vocabulary"""
    if "gpt2" in model.config.architectures[0].lower():
        with torch.inference_mode():
            vocab = torch.matmul(embed, model.wte.weight.t())
            if logits:
                return vocab
            return lsm(vocab) if log else sm(vocab)
    elif "llama" in model.config.architectures[0].lower():
        assert False, "Support for LLaMA is not here yet"


def print_forward_hooks(main_module):
    """Function to print forward hooks of a module and its sub-modules"""
    for name, submodule in main_module.named_modules():
        if hasattr(submodule, "_forward_hooks") and submodule._forward_hooks:
            print(f"Module: {name if name else 'Main Module'}")
            for hook_id, hook in submodule._forward_hooks.items():
                print(f"  ID: {hook_id}, Hook: {hook}")

        if hasattr(submodule, "_forward_pre_hooks") and submodule._forward_hooks:
            print(f"Module: {name if name else 'Main Module'}")
            for hook_id, hook in submodule._forward_pre_hooks.items():
                print(f"  ID: {hook_id}, Hook: {hook}")
                

def remove_forward_hooks(main_module: nn.Module):
    """Function to remove all forward and pre-forward hooks from a module and its sub-modules."""
    
    # Remove forward hooks
    for _, submodule in main_module.named_modules():
        if hasattr(submodule, "_forward_hooks"):
            hooks = list(submodule._forward_hooks.keys())  # Get a list of hook IDs
            for hook_id in hooks:
                submodule._forward_hooks.pop(hook_id)
        
        # Remove pre-forward hooks
        if hasattr(submodule, "_forward_pre_hooks"):
            pre_hooks = list(submodule._forward_pre_hooks.keys())  # Get a list of pre-hook IDs
            for pre_hook_id in pre_hooks:
                submodule._forward_pre_hooks.pop(pre_hook_id)
                
def set_seed(seed: int):
    """Set seed. Deprecate soon since it is in the huggingface library"""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def sigmoid_boundary(_input, boundary_x, boundary_y, temperature):
    """Generate sigmoid mask"""
    return torch.sigmoid((_input - boundary_x) / temperature) * \
        torch.sigmoid((boundary_y - _input) / temperature)


def harmonic_sigmoid_boundary(_input, boundary_x, boundary_y, temperature):
    """Generate harmonic sigmoid mask"""
    return (_input<=boundary_x)*torch.sigmoid((_input - boundary_x) / temperature) + \
    (_input>=boundary_y)*torch.sigmoid((boundary_y - _input) / temperature) + \
    ((_input>boundary_x)&(_input<boundary_y))*torch.sigmoid(
        (0.5 * (torch.abs(_input - boundary_x)**(-1) + torch.abs(_input - boundary_y)**(-1)))**(-1) / temperature
    )


def count_parameters(model):
    """Count parameters of a model that require gradients"""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def random_permutation_matrix(n):
    """Generate a random permutation matrix"""
    P = torch.eye(n)
    perm = torch.randperm(n)
    P = P[perm]
    
    return P


def closeness_to_permutation_loss(R):
    """Measure how close a rotation m is close to a permutation m"""
    row_sum_diff = torch.abs(R.sum(dim=1) - 1.0).mean()
    col_sum_diff = torch.abs(R.sum(dim=0) - 1.0).mean()
    entry_diff = (R * (1 - R)).mean()
    loss = .5 * (row_sum_diff + col_sum_diff) + entry_diff
    return loss


def format_token(tokenizer, tok):
    """Format the token for some path patching experiment to show decoding diff"""
    return tokenizer.decode(tok).replace(" ", "_").replace("\n", "\\n")


def top_vals(tokenizer, res, n=10):
    """Pretty print the top n values of a distribution over the vocabulary"""
    top_values, top_indices = torch.topk(res, n)
    for i in range(len(top_values)):
        tok = format_token(tokenizer, top_indices[i].item())
        print(f"{tok:<20} {top_values[i].item()}")
