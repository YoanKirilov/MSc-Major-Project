// Pure ownership/recovery state. No DOM, storage, timers, permission or requests.
export function createStartState(initial = null) {
  let operation = initial;
  let generation = 0;
  let activeRead = null;
  let reads = 0;
  const owns = (id, version) => operation === id && generation === version;
  return {
    get operation() { return operation; },
    get generation() { return generation; },
    owns,
    select(id) {
      if (id === operation) return false;
      operation = id;
      generation += 1;
      reads = 0;
      return true;
    },
    beginRead() {
      if (!operation || (activeRead && owns(activeRead.operation, activeRead.generation))) return null;
      activeRead = Object.freeze({ operation, generation });
      return activeRead;
    },
    finishRead(read) {
      if (activeRead !== read) return false;
      activeRead = null;
      return owns(read.operation, read.generation);
    },
    shouldPoll(read) {
      return owns(read.operation, read.generation) && ++reads < 10;
    },
    resetReads() { reads = 0; },
  };
}
