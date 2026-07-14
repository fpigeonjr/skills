# Code Smell Baseline

Use these as review heuristics, not hard rules. A documented repository standard overrides them, and tooling-enforced style should not be reported manually.

- **Mysterious Name**: A name does not reveal what the value, function, or type represents. Prefer a name that exposes its role; an object that cannot be named clearly may need redesign.
- **Duplicated Code**: The same logic shape appears in multiple changed locations. Extract the shared behavior when doing so makes the concept clearer.
- **Feature Envy**: A function works more with another object's data than its own. Move the behavior closer to the data it uses.
- **Data Clumps**: The same fields or parameters repeatedly travel together. Consider representing the group as a domain type.
- **Primitive Obsession**: A primitive stands in for a meaningful domain concept. Consider a small type that enforces the concept's rules.
- **Repeated Switches**: Conditional dispatch on the same discriminator recurs. Centralize the dispatch or use an appropriate polymorphic design.
- **Shotgun Surgery**: One conceptual change requires scattered edits across many modules. Gather the behavior behind a stable interface.
- **Divergent Change**: One module changes for several unrelated reasons. Separate the responsibilities that evolve independently.
- **Speculative Generality**: An abstraction, option, or extension point has no current requirement. Remove it until a concrete need exists.
- **Message Chains**: Callers navigate through a long chain of objects. Hide the navigation behind a meaningful operation.
- **Middle Man**: A type or function mostly delegates without adding a useful boundary. Remove it or give the boundary a substantive responsibility.
- **Refused Bequest**: A subtype ignores or rejects much of its inherited contract. Prefer composition or a narrower abstraction.
