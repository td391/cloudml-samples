# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the \"License\");
# you may not use this file except in compliance with the License.\n",
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an \"AS IS\" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import torch
import torch.optim as optim
import torch.nn as nn

import data_utils
import model


def train(net, train_loader, optimizer, epoch):
    """Create the training loop"""
    net.train()
    criterion = nn.BCELoss()
    running_loss = 0.0

    for batch_index, data in enumerate(train_loader):
        features = data['features']
        target = data['target']

        # zero the parameter gradients
        optimizer.zero_grad()
        # forward + backward + optimize
        outputs = net(features)
        loss = criterion(outputs, target)
        loss.backward()
        optimizer.step()

        # print statistics
        running_loss += loss.item()
        if batch_index % 6 == 5:  # print every 6 mini-batches
            print('[%d, %5d] loss: %.3f' %
                  (epoch, batch_index + 1, running_loss / 6))
            running_loss = 0.0


def set_value_(item):
    """Take the predictions and assign them a binary target value."""
    if item < 0.5:
        return 0.0
    else:
        return 1.0


def test(net, test_loader):
    """Test the DNN"""
    net.eval()
    criterion = nn.BCELoss()
    test_loss = 0
    correct = 0

    with torch.no_grad():
        for i, data in enumerate(test_loader, 0):
            features = data['features']
            target = data['target']
            output = net(features)
            # Binarize the output
            pred = output.apply_(set_value_)

            test_loss += criterion(output, target)  # sum up batch loss

            correct += pred.eq(target.view_as(pred)).sum().item()

    test_loss /= len(test_loader.dataset)
    print('\nTest set:\n\tAverage loss: {:.4f}'.format(test_loss))
    print('\tAccuracy: {}/{} ({:.0f}%)\n'.format(
            correct,
            (len(test_loader) * test_loader.batch_size),
            100. * correct / (len(test_loader) * test_loader.batch_size)))


def task(args):
    """Load the data, train the model, test the model, export / save the model
    """
    torch.manual_seed(args.seed)

    # Open our dataset
    train_loader, test_loader = data_utils.load_data(args.test_split,
                                                     args.batch_size)

    # Create the model
    net = model.SonarDNN().double()
    optimizer = optim.SGD(net.parameters(), lr=args.lr,
                          momentum=args.momentum, nesterov=False)

    # Train / Test the model
    for epoch in range(1, args.epochs + 1):
        train(net, train_loader, optimizer, epoch)
        test(net, test_loader)

    if args.model_name:
        # Export the trained model
        torch.save(net.state_dict(), args.model_name)

        if args.model_dir:
            # Save the model to GCS
            data_utils.save_model(args.model_dir, args.model_name)


def main():
    # Training settings
    parser = argparse.ArgumentParser(description='PyTorch Sonar Example')
    parser.add_argument('--model-dir',
                        type=str,
                        help='Where to save the model')
    parser.add_argument('--model-name',
                        type=str,
                        default='sonar_model',
                        help='What to name the saved model file')
    parser.add_argument('--batch-size',
                        type=int,
                        default=4,
                        help='input batch size for training (default: 4)')
    parser.add_argument('--test-split',
                        type=float,
                        default=0.2,
                        help='split size for training / testing dataset')
    parser.add_argument('--epochs',
                        type=int,
                        default=10,
                        help='number of epochs to train (default: 10)')
    parser.add_argument('--lr',
                        type=float,
                        default=0.01,
                        help='learning rate (default: 0.01)')
    parser.add_argument('--momentum',
                        type=float,
                        default=0.5,
                        help='SGD momentum (default: 0.5)')
    parser.add_argument('--seed',
                        type=int,
                        default=42,
                        help='random seed (default: 42)')
    args = parser.parse_args()

    task(args)


if __name__ == '__main__':
    main()
