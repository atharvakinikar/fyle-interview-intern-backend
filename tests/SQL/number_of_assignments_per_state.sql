-- Write query to get number of assignments for each state
SELECT state, COUNT(*) as num_assignments FROM assignments GROUP BY state;