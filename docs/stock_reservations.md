# Stock Reservations

This slice records approved stock reservation claims for jobs.

Each append-only record references an item, quantity, location, job, and verified reserver. Recording a reservation does not decrement stock, relocate materials, purchase supplies, or confirm physical availability.

Later stock-count and movement layers must use separate contracts and receipts.