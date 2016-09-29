# PSM - Python State Machine

# Description
This is a framework for defining state machines using Python.

Inputs to the state machine should be evaluated on transition states and outputs should be evaluated on states (Moore).
___
# Structure
![Structure](https://github.com/omf/psm/blob/master/images/psm.png)
___
# Workflow
Every time StateMachine.run() is invoked:

    1. StateMachine runs the current state.
    2. If the result of the previous StateMechine execution current state is different from previous one, StateMachine invokes current State's _enter() method and, after that, invokes State's run() method.
    3. The State runs it's defined task (if any) and, after that, evaluates if a transition should be followed.
    4. Each StateTransition evaluates it's conditions and, if any of them evaluates to true, returns the next State.
    5. State returns the next State to StateMachine or itself if no StateTransition should be followed.
    6. If the returned State is different from the current one, StateMachine invokes current State's _leave() method.
___
# Classes
## StateMachine
Manage the StateMachine life cycle. Can contain States/varibles/parameters/functions.

Members:

  - `StateMachine(id)`
  - `add_state(state)`
  - `get_state(id)`
  - `set_initial_state(state)`
  - `run()`
  
## State
![Structure](https://github.com/omf/psm/blob/master/images/state.png)

A State.

Members:

  - `State(id, sateMachine)`: takes an id and the parent StateMachine object
  - `run(stateMachine)`: invoked by stateMachine on every StateMachine step. Evaluates all the State's StateTransitions and runs the asigned task.
  - `set_stay_transition(stateTransition)`: assigns the loop StateTransition. That is, the transition that is evaluated after the rest of transitions are evaluated and none of them is going to be followed.
  - `add_state_transition(stateTransition, toState)`: adds a stateTransition and the state that should be followed if stateTransition evaluates to true.
  - `_enter(stateMachine)`: invoked when stateMachine enters this State
  - `_leave(stateMachine)`: invoked when stateMachine exits this State
  - `task(stateMachine)`: task to always run in every execution.


## StateTransition
![Structure](https://github.com/omf/psm/blob/master/images/transition.png)

A state transition.

Members:
  - `StateTransition(id)`
  - `log_once()`: tells the transition to only log once wether the condition/s evaluation is true.
  - `add_condition(condition)`: adds a TransitionCondition. Adding more than one condition implies an AND operation between them.
  - `follow(stateMachine)`: evals the assigned conditions and returning the next state.
 
## TransitionCondition [interface]
![Structure](https://github.com/omf/psm/blob/master/images/condition.png)

A transition condition. Must inherit from this class and override evaluate() and/or reset() methods. The same condition object can be reused in differente StateTransition objects.

Members:

  - `TransitionCondition(id)`
  - `evaluate(stateMachine)`: overriden to perform the needed operations. Must return True or False
  - `reset(stateMachine)`: overriden to perform any kind of setup or reset operation before `evaluate()` is executed.

As they receive a StateMachine as parameter any variable or function belonging to that StateMachine can be used by the TransitionCondition.

## LambdaCondition(TransitionCondition)

A oneliner condition.

Miembros:

  - `LambdaCondition(id, lambda)`: receives the lambda expression.

Typically:
  - `lambda SM: <expression over SM>`

ie:
  - `lambda SM: SM.i == 0`

## Notes
  - A State belongs to one and only one StateMachine
  - A StateTransition belongs to one and only one State
  - A TransitionCondition (if it doesn't preserve any state) can be shared between different States.

___
# Built-in Types
Note: a red arrow is an entry point.

## TrueCondition
![Structure](https://github.com/omf/psm/blob/master/images/true.png)

Always returns true. Forces a transition between two states

## FalseCondition
![Structure](https://github.com/omf/psm/blob/master/images/false.png)

Always returns zero. Does nothing.

## OneShotWaitCondition
![Structure](https://github.com/omf/psm/blob/master/images/oneshotwait.png)

Decrements counter 't' until zero. At zero returns False.

## PassThrough
![Structure](https://github.com/omf/psm/blob/master/images/passthrough.png)

It's composed by a State and one TrueCondition. Used to perform some operations and continue to the next state.

Members:

  - `PassthroughState(id, stateMachine, toState)`: `toState` is the next state

## WaitState
![Structure](https://github.com/omf/psm/blob/master/images/wait.png)

Using OneShotWaitCondition, represents a waiting state that doesn't stop the StateMachine execution (it waits 'ticks' not time).

Members:

  - `WaitState(id, stateMachine, timeout, toState)`: `timeout` is, actually, how many execution ticks to wait. `toState` is the next state.

## RetryState
![Structure](https://github.com/omf/psm/blob/master/images/retry.png)

Composed by a OneShotWaitCondition, an OK condition, an Error/Retry condition and the OK, RETRY and ERROR states plus a wating time and number of retries.

Performs a number of operations 'number of retries' times waiting 'wating time' between retries.

Conditions:

  - OKCondition == true -> transition to OK state
  - RetryErrorCondition == true & remaining retries -> transition to RETRY
  - RetryErrorCondition == true & run out of retries -> transition to ERROR

Members:

 - `RetryState(id, stateMachine, timeout, retries)`
 - `set_ok_transition(okCondition, toState)`
 - `set_retry_error_transition(retryErrorCondition, retryToState, errorToState)`
___
# Example: Flip-Flop
![Structure](https://github.com/omf/psm/blob/master/images/flipflop.png)

Element identification:
- states: 
  - two: A and B
- transitions:
  - four: a loop in A, a loop in B, a transition from A to B and a transition from B to A.
- conditions:
  - two: i == 0, i == 1

Steps:

    1. States are created
    2. Transitions are created
    3. Conditions are created
    4. Conditions are assigned to Transitions
    5. Transitions are assigned to States
    6. An initial state is specified

Code:

    import epsm
    
    class FlipFlop(StateMachine):
        def __init__(self, id):
            self.i = 0 # state machine variable
    
            self._initStateMachine()
    
    
        def _initStateMachine(self):
            # two states
            A = State("A", self)
            B = State("B", self)
    
            # four transitions
            stayA = StateTransition("stayA")
            stayB = StateTransition("stayB")
            aToB = StateTransition("A to B")
            bToA = StateTransition("B to A")
    
    # two conditions
    i0 = LambdaCondition("i == 0", lambda SM: SM.i == 0)
    i1 = LambdaCondition("i == 1", lambda SM: SM.i == 1)
    
    # assinging conditions to transitions
    stayA.add_condition(i0)
    stayB.add_condition(i1)
    aToB.add_condition(i1)
    bToA.add_condition(i0)
    
    # assinging transitions to states
    A.set_stay_transition(stayA)
    A.add_state_transition(aToB, B)
    B.set_stay_transition(stayB)
    B.add_state_transition(bToA, A)
    
    self.set_initial_state(A)
    
Test:

    ...

    flipflop = FlipFlop("FLIPFLOP")

    ...


    # initial state is A
    # stay in state A
    flipflop.i = 0
    flipflop.run()
    flipflop.run()
    flipflop.run()
    
    # state change due to "i == 1"
    flipflop.i = 1
    flipflop.run() # logs the full transition
    flipflop.run() # logs entering A
    flipflop.run() # logs staying in B
    
    # state change due to "i == 0"
    flipflop.i = 0
    flipflop.run()
    flipflop.run()
    flipflop.run()
    
