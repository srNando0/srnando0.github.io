'''

	Longest Palindrome Substring

+----------------
| Input : an string
| Output: a longest palindrome substring (not unique, rightmost)
+----------------
| Time  Complexity: O(n^2)
| Space Complexity: O(n)
+----------------
'''
def longestPalindrome(string):
	size = len(string)	# size of string
	
	# Empty string case
	if size == 0:
		return ''
	
	# Declarations
	tabulation = [	# Tabulation: 0 for k even, 1 for k odd
		[True for _ in range(size)],
		[True for _ in range(size)]
	]
	
	start = size - 1	# start position of the palindrome in string
	length = 1			# length of the palindrome
	
	# Recursion: string[i : j] is a palindrome if, and only if, string[i] == string[j] and string[i + 1: j - 1] is a palindrome as well
	for k in range(1, size):
		for i in range(size - k):
			# Check if string[i] == string[j]
			if string[i] == string[i + k]:
				# Check if string[i + 1 : j - 1] is a palindrome
				if tabulation[k%2][i + 1]:
					# string[i : j] must be a palindrome as well
					tabulation[k%2][i] = True
					start = i
					length = k + 1
			# Otherwise, string[i : j] is not a palindrome
			else:
				tabulation[k%2][i] = False
	
	# Return the palindrome
	return string[start : start + length]



'''

	Main

'''
print(longestPalindrome(input()))