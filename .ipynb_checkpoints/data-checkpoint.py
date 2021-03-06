import torch
import torchvision
import torchvision.transforms as transforms

class Data:
    """This class contains the attributes that all datasets have in common.
    All datasets will inherit from this class.
    
    ...
    Attributes
    ----------
    train_loader : PyTorch Dataloader
        The dataloader for the training set
    train_loader : PyTorch Dataloader
        The dataloader for the testing set
    data_x_dim : int
        The size of the x-dimension for each image in the dataset
    data_y_dim : int
        The size of the y-dimension for each image in the dataset  
    """
    
    def __init__(self):
        self.train_loader = None
        self.test_loader = None
        self.data_x_dim = None
        self.data_y_dim = None

#     @property
#     @abstractmethod
#     def train_loader(self):
#         raise NotImplementedError

#     @property
#     def test_loader(self):
#         raise NotImplementedError

#     @property
#     def data_x_dim(self):
#         raise NotImplementedError

#     @property
#     def data_y_dim(self):
#         raise NotImplementedError
        

class MNIST(Data):
    """The MNIST Dataset (Handwritten Digits)
    
    ...
    Attributes
    ----------
    train_loader : PyTorch Dataloader
        The dataloader for the training set
    train_loader : PyTorch Dataloader
        The dataloader for the testing set
    data_x_dim : int
        The size of the x-dimension for each image in the dataset
    data_y_dim : int
        The size of the y-dimension for each image in the dataset
    train_batch_size : int
        The number of training examples per batch
    test_batch_size : int
        The number of testing examples per batch
    dataloaders : dict
        A dictionary that contains the 2 dataloaders. The keys are 
        "train" and "test"
    """
    
    def __init__(self, train_batch=64, test_batch=64):
        self.train_batch_size = train_batch
        self.test_batch_size = test_batch
        
        self.train_loader = torch.utils.data.DataLoader( 
                                torchvision.datasets.MNIST('./data', 
                                   train=True, 
                                   download=True,
                                   transform=torchvision.transforms.Compose([
                                       torchvision.transforms.ToTensor(),
                                       torchvision.transforms.Normalize((0.1307,), (0.3081,))])),
                                batch_size=self.train_batch_size, shuffle=True)
        
        dataset = torch.utils.data.Subset(self.train_loader.dataset, range(0, 4000))
        
        self.train_loader = torch.utils.data.DataLoader(dataset, batch_size=self.train_batch_size, 
                                                        shuffle=True)
        
        self.test_loader = torch.utils.data.DataLoader( 
                        torchvision.datasets.MNIST('./data', 
                           train=False, 
                           download=True,
                           transform=torchvision.transforms.Compose([
                               torchvision.transforms.ToTensor(),
                               torchvision.transforms.Normalize((0.1307,), (0.3081,))])),
                        batch_size=self.test_batch_size, shuffle=False)
        
        # Only use a subset of the MNIST dataset for MLP
        self.dataloaders = {'train': self.train_loader,
                            'test': self.test_loader}
        
        self.data_x_dim = self.train_loader.dataset[0][0].shape[1]
        self.data_y_dim = self.train_loader.dataset[0][0].shape[2]
        
#         @property
#         def train_batch_size(self):
#             return self.train_batch_size
        
#         @property
#         def test_batch_size(self):
#             return self.test_batch_size

#         @property
#         def test_loader(self):
#             return self.test_loader
        
#         @property
#         def data_x_dim(self):
#             return self.train_loader.dataset[0][0].shape[1]

#         @property
#         def data_y_dim(self):
#             return self.train_loader.dataset[0][0].shape[2]