# Levenshtein text distance
def levenshtein(a: str, b: str) -> int:
    a_len = len(a)
    b_len = len(b)
    if a_len == 0 or b_len == 0:
        return a_len + b_len
    
    matrix = []
    # increment along the first column of each row
    for i in range(0, b_len + 1):
        matrix.append([i])
        
    # increment each column in the first row
    for j in range(1, a_len + 1):
        matrix[0].append(j)

    # Fill in the rest of the matrix
    for i in range(1, b_len + 1):
        matrix[i].extend([0] * (a_len))
        for j in range(1, a_len + 1):
            substitution_cost = 0 if b[i - 1] == a[j - 1] else 1
            matrix[i][j] = min(
                matrix[i-1][j-1] + substitution_cost, # substitution                
                matrix[i][j-1] + 1, # insertion
                matrix[i-1][j] + 1  # deletion
            )

    return matrix[b_len][a_len]