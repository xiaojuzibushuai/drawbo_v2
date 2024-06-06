'''
最长连续序列 20240218 xiaojuzi
'''
def longestConsecutive(self, nums: list[int]) -> int:
    
    # 去重 第一次不去重直接超时了- -
    num_set = set(nums)
    max_length = 0
    
    for num in num_set:
        if num - 1 not in num_set:
            cur_num = num
            cur_length = 1
            while cur_num+1 in num_set:
                cur_num += 1
                cur_length += 1
            max_length = max(max_length,cur_length)
            
    return max_length

'''
盛最多水的容器 20240218 xiaojuzi
'''
def maxArea(self, height: list[int]) -> int:
    max_area = 0
    left = 0
    right = len(height) - 1
    while left < right:
        max_area = max(min(height[left], height[right]) * (right - left), max_area)
        if height[left]<height[right]:
            left += 1
        else:
            right -= 1
    return max_area


'''
接雨水 20240218 xiaojuzi
'''
def trap(self, height: list[int]) -> int:
    left, right = 0, len(height) - 1
    left_max, right_max = height[left], height[right]
    water = 0

    while left<right:
        left_max = max(left_max, height[left])
        right_max = max(right_max, height[right])

        if left_max < right_max:
            water += left_max - height[left]
            left += 1
        else:
            water += right_max - height[right]
            right -= 1

    return water

def numIslands(self, grid: list[list[str]]) -> int:
    def dfs(grid,i,j):
        if grid[i][j] == '0':
            return
        grid[i][j] = '0'
        dfs(grid, i - 1, j)
        dfs(grid, i + 1, j)
        dfs(grid, i, j - 1)
        dfs(grid, i, j + 1)

    def bfs(grid,i,j):
        queue = collections.deque([(i, j)])
        grid[i][j] = '0'
        while queue:

            x, y = queue.popleft()
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            for dx, dy in directions:
                new_x, new_y = x + dx, y + dy
                if 0 <= new_x < rows and 0 <= new_y < cols and grid[new_x][new_y] == '1':
                    queue.append((new_x, new_y))
                    grid[new_x][new_y] = '0'

    if not grid:
        return 0

    rows, cols = len(grid), len(grid[0])
    res = 0
    for i in range(rows):
        for j in range(cols):
            if grid[i][j] == '1':
                res += 1
                dfs(grid,i,j)
    return res









