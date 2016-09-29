# Copyright (c) 2016 Oscar Martinez
# omartinezfer@gmail.com
# 
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 

import logging


class Element():
    id      = None
    _logger = None

    def __init__(self, id):
        self.id = id
        self._logger = initLogger(self.__class__.__name__, self.id)

    def initLogger(*loggerName):
        logger = logging.getLogger('.'.join(map(str, loggerName)))
        return logger



class TransitionCondition(Element):

    def __init__(self, id):
        Element.__init__(self, id)
        
    def evaluate(self, stateMachine):
        pass
    
    def reset(self, stateMachine):
        pass

class LambdaCondition(TransitionCondition):
    lmbd = None
    
    def __init__(self, id, lmbd):
        TransitionCondition.__init__(self, id)
        self.lmbd = lmbd
        
    def evaluate(self, stateMachine):
        val = self.lmbd(stateMachine)
        stateMachine._logger.debug("evaluating: '%s' = %d", self.id, val)
        return val

class NegateOperation(TransitionCondition):
    def __init__(self, id, conditionInstance):
        self.condition_instance = conditionInstance

    def evaluate(self, stateMachine):
        return not self.condition_instance.evaluate(stateMachine)
        
class StateTransition(Element):
    delay = None
    conditions = None
    _logged = None
    
    def __init__(self, id):
        Element.__init__(self, id)
        self.conditions = []
        self.delay = 0
        self._logged = None
        self.to_state = None
        self.from_state = None
    
    def log_once(self):
        self._logged = False
        
    def add_condition(self, condition):
        self.conditions.append(condition);
        
    def follow(self, stateMachine):
        _should_follow = True
        _true_conditions = []

        for c in self.conditions:
            _should_follow = _should_follow and c.evaluate(stateMachine)
            if _should_follow == True: _true_conditions.append(c.id)

        if _should_follow and not self._logged:
            stateMachine._logger.info("from %s to %s due to %s", self.from_state.id, self.to_state.id, " && ".join(_true_conditions))
            #stateMachine._logger.info("from %s to %s due to %s", self.from_.id, self.to.id, c.id)
            if self._logged != None: self._logged = True

        return _should_follow


class State(Element):
    to_states = None
    transitions = None
    stay_transition = None

    def __init__(self, id, stateMachine):
        Element.__init__(self, id)
        self.to_states = []
        self.transitions = []
        self.stay_transition = None
        stateMachine.add_state(self)
        
    def _enter(self, stateMachine):
        stateMachine._logger.info("entering state: %s", self.id)
        if self.stay_transition != None: self.stay_transition.log_once()
        
    def _leave(self, stateMachine):
        stateMachine._logger.info("leaving state: %s", self.id)
        
    def add_state_transition(self, transition, to):
        if to == None: to = self
        if transition.to_state != None or transition.from_state != None:
            # TODO: throw
            self._logger.error("transition %s in use!!!", transition.id)
        self.to_states.append(to)
        transition.from_state = self
        transition.to_state = to
        self.transitions.append(transition)

    def set_stay_transition(self, transition):
        self.stay_transition = transition
        self.stay_transition.from_state = self
        self.stay_transition.to_state = self
        self.stay_transition.log_once()
        
    def task(self, stateMachine):
        pass
        
    def run(self, stateMachine):
        #self._logger.error("RUN: %s", self.id)
        self.task(stateMachine)
        
        for i in range(0, len(self.transitions)):
            tr = self.transitions[i]
            if tr.follow(stateMachine):
                return self.to_states[i]

        if self.stay_transition != None and self.stay_transition.follow(stateMachine): return self

        # TODO: throw
        stateMachine._logger.error("NOT FOLLOWING any transition")
            
        return None   


class StateMachine(Element):
    STATUS_OK = 0
    STATUS_ERROR = 1
    STATUS_ERROR_CSN = 2
    STATUS_ERROR_PSN = 3
   
    def __init__(self, id):
        Element.__init__(self, id)
        self.states = {}
        self.prev_state = None
        self.current_state = None
        self.status = self.STATUS_OK
        self.on_error_goto_state = None
 

    def _trace_transitions(self, state):
        self._logger.error("-- STARTING state %s transitions dump. Setting debug level to DEBUG", state.id)
        self._logger.setLevel("DEBUG")

        for tr in state.transitions:
            self._logger.debug("-- evaluating: %s", tr.id)
            ret = tr.follow(self)
            self._logger.debug("result: %d", ret)

        state.stay_transition.follow(self)

        self._logger.debug("-- END %d", self.automatico)

    def _error(self, errorId, errorDesc, traceState):
        self._logger.error(errorDesc)
        self.status = errorId
        self._trace_transitions(traceState)
        if self.on_error_goto_state != None: self.current_state = self.on_error_goto_state

    def add_state(self, state):
        self.states[state.id] = state

    def get_state(self, id):
        return self.states[id]
        
    def set_initial_state(self, state):
        self.current_state = state

    def run(self):
        if self.current_state != self.prev_state:
            if self.current_state != None:
                self.current_state._enter(self)
            # TODO: throw
            else:
                """self._logger.error("CURRENT STATE NONE!!")
                self.status = self.STATUS_ERROR_CSN #current state none
                self._trace_transitions(self.prev_state)
                if self.on_error_goto_state != None: self.current_state = self.on_error_goto_state"""
                self._error(self.STATUS_ERROR_CSN, "CURRENT STATE NONE!!", self.prev_state)

        # if self.current_state == None: return
            
        state = self.current_state.run(self)
        self.prev_state = self.current_state
        self.current_state = state

        if self.current_state != self.prev_state:
            if self.prev_state != None:
                self.prev_state._leave(self)
            # TODO: throw
            else:
                """self._logger.error("PREV STATE NONE!!")
                self.status = self.STATUS_ERROR_PSN #previous status none
                self._trace_transitions(self.current_state)
                if self.on_error_goto_state != None: self.current_state = self.on_error_goto_state"""
                self._error(self.STATUS_ERROR_PSN, "PREV STATE NONE!!", self.current_state)




        
# Builtin state types
class TrueCondition(TransitionCondition):
    def evaluate(self, stateMachine):
        return True

class FalseCondition(TransitionCondition):
    def evaluate(self, stateMachine):
        return False

# Passthrough
class PassthroughState(State):
    def __init__(self, id, stateMachine, toState):
        State.__init__(self, id, stateMachine)
        
        tr = StateTransition("passing-through")
        tr.add_condition(TrueCondition("True"))
        self.add_state_transition(tr, toState)
        
# Simple wait state
class OneShotWaitCondition(TransitionCondition):
    _wait = None
    _wait_count = None
    
    def set_timeout(self, timeout):
        self._wait = timeout
        self._wait_count = timeout
        
    def evaluate(self, stateMachine):
        self._wait_count -= 1
        #self._logger.info("%d", self._wait_count)
        return not (self._wait_count < 0)
        
    def reset(self, stateMachine):
        stateMachine._logger.info("waiting for %d ticks ...", self._wait)
        self._wait_count = self._wait

class WaitState(State):
    wait_condition = None
    
    def __init__(self, id, stateMachine, timeout, to):
        State.__init__(self, id, stateMachine)
        self.wait_condition = OneShotWaitCondition("OneShotWait")
        self.wait_condition.set_timeout(timeout)
        
        wait_transition = StateTransition("1")
        wait_transition.add_condition(self.wait_condition)
        true_transition = StateTransition("True")
        true_transition.add_condition(TrueCondition("True"))
        
        self.add_state_transition(wait_transition, self)
        self.add_state_transition(true_transition, to)

    def _enter(self, stateMachine):
        State._enter(self, stateMachine)
        self.wait_condition.reset(stateMachine)
        
# Wait state + retries        
class RetryState(State):
    retries = 0
    _retries_counter = 1

    class _OkAndResetCondition(TransitionCondition):
        def evaluate(self, stateMachine):
            #if(stateMachine.current_state._retries_counter > stateMachine.current_state.retries):
            stateMachine.current_state._retries_counter = 1
            return True

    class _ErrorAndResetCondition(TransitionCondition):
        def evaluate(self, stateMachine):
            if(stateMachine.current_state._retries_counter > stateMachine.current_state.retries):
                stateMachine.current_state._retries_counter = 1
                return True
            return False

    def __init__(self, id, stateMachine, timeout, retries):
        State.__init__(self, id, stateMachine)
        
        self.wait_condition = OneShotWaitCondition("OneShotWait")
        self.wait_condition.set_timeout(timeout)
        self.wait_transition = StateTransition("Waiting")
        self.wait_transition.add_condition(self.wait_condition)
        self.add_state_transition(self.wait_transition, self)

        self.retries = retries
        self._retries_counter = 1

    def _enter(self, stateMachine):
        State._enter(self, stateMachine)
        
        stateMachine._logger.info("Try: %d", self._retries_counter)
        self._retries_counter += 1

        self.wait_condition.reset(stateMachine)
        self.wait_transition.log_once()

    def set_ok_transition(self, okCondition, toState):            
        _ok_transition = StateTransition("OK")
        _ok_transition.add_condition(okCondition)
        _ok_transition.add_condition(self._OkAndResetCondition("ok & reset"))
        self.add_state_transition(_ok_transition, toState)

    def set_retry_error_transition(self, condition, retryToState, errorToState):
        _retry_transition = StateTransition("RETRY")
        _retry_transition.add_condition(condition)
        _retry_transition.add_condition(LambdaCondition("retries < %d" % self.retries, lambda SM: SM.current_state._retries_counter <= SM.current_state.retries))
        self.add_state_transition(_retry_transition, retryToState)

        _error_transition = StateTransition("ERROR")
        _error_transition.add_condition(condition)
        _error_transition.add_condition(self._ErrorAndResetCondition("retries > %d" % self.retries))
        self.add_state_transition(_error_transition, errorToState)



