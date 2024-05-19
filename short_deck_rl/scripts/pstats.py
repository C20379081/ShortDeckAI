import pstats

# Load the statistics from the file
stats = pstats.Stats('__pycache__/profile.cprof')

# Clean up filenames for the report
stats.strip_dirs()

# Sort the statistics by the cumulative time spent in the function
stats.sort_stats('cumulative')

# Print the top 10 functions
stats.print_stats(10)

# Sort the statistics by the total time spent in the function
stats.sort_stats('time')

# Print the top 10 functions
stats.print_stats(10)

