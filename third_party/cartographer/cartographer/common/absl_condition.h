#ifndef CARTOGRAPHER_COMMON_ABSL_CONDITION_H_
#define CARTOGRAPHER_COMMON_ABSL_CONDITION_H_

#include "absl/synchronization/mutex.h"

namespace cartographer {
namespace common {

// Abseil 2026 no longer accepts capturing lambdas via Condition(&lambda).
template <typename Predicate>
bool CallPredicate(void* arg) {
  return (*static_cast<const Predicate*>(arg))();
}

template <typename Predicate>
absl::Condition MakeCondition(const Predicate* predicate) {
  return absl::Condition(
      &CallPredicate<Predicate>,
      const_cast<void*>(static_cast<const void*>(predicate)));
}

}  // namespace common
}  // namespace cartographer

#endif  // CARTOGRAPHER_COMMON_ABSL_CONDITION_H_
