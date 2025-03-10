# Transaction Manager

The Transaction Manager coordinates the execution of transactions across multiple files, handling conflict resolution, and enforcing resource limits.

## High-level Concept

Since all node operations are on byte positions of the original file, multiple operations that change the total byte length of the file will result in offset errors and broken code.

Give this example over here:

```
Original: FooBar
Operations: Remove "Foo" (bytes 0-3), Insert "Hello" (bytes 0-5)
            Remove "Bar" (bytes 3-6), Insert "World" (bytes 3-7)
```

If these operations were applied in order, the result would be:

```
Result: FooBar
Operation: Remove "Foo" (bytes 0-3), Insert "Hello" (bytes 0-5)
Result: HelloBar
Operation: Remove "Bar" (bytes 3-6), Insert "World" (bytes 3-7)
Result: HelWorldar
```

Resulting in an invalid output.

⭐ The key with TransactionManager is that it queues up all transactions in a given Codemod run, the applies all of the ***backwards*** from the last byte range to the first. Given the same example as above but applied backwards:

```
Result: FooBar
Operation: Remove "Bar" (bytes 3-6), Insert "World" (bytes 3-7)
Result: FooWorld
Operation: Remove "Foo" (bytes 0-3), Insert "Hello" (bytes 0-5)
Result: HelloWorld
```

TransactionManager also performs some additional operations such detecting conflicts and coordinating (some basic) conflict resolutions. Overall, the core responsibilities are as follows:

1. **Transaction Queueing**: Maintains a queue of pending transactions organized by file
1. **Conflict Resolution**: Detects and resolves conflicts between transactions
1. **Transaction Execution**: Applies transactions in the correct order
1. **Resource Management**: Enforces limits on transaction count and execution time
1. **Change Tracking**: Generates diffs for applied changes

## Sorting Transactions

Before execution, transactions are sorted based on (in this priority):

1. Position in the file (higher byte positions first)
1. Transaction type (following the priority order)
1. User-defined priority
1. Creation order

This sorting ensures that transactions are applied in a deterministic order that minimizes conflicts. Larger byte ranges are always edited first, removals happen before insertions, and older transactions are applied before newer ones.

## Conflict Resolution

### Conflict Types

The manager identifies several types of conflicts:

1. **Overlapping Transactions**: Multiple transactions affecting the same byte range
1. **Contained Transactions**: One transaction completely contained within another
1. **Adjacent Transactions**: Transactions affecting adjacent byte ranges

In it's current implementation, TransactionManager only handles Contained Transactions that are trivially sovable. (If a remove transaction completely overlaps with another remove transaction, only the larger one will be kept)

## Resource Management

The Transaction Manager enforces two types of limits:

1. **Transaction Count**: Optional maximum number of transactions
1. **Execution Time**: Optional time limit for transaction processing

These limits prevent excessive resource usage and allow for early termination of long-running operations.

## Commit Process

The commit process applies queued transactions to the codebase:

1. Transactions are sorted according to priority rules
1. Files are processed one by one
1. For each file, transactions are executed in order
1. Diffs are collected for each modified file
1. The queue is cleared after successful commit

The diff's are later used during resyc to efficiently update the codebase graph as changes occur. See [Incremental Computation](../6.%20incremental-computation/A.%20Overview.md) for more details.

## Next Step

After managing transactions, the system handles [Incremental Computation](../6.%20incremental-computation/A.%20Overview.md) to efficiently update the codebase graph as changes occur.
