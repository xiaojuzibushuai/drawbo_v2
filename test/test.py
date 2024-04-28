
import collections
import heapq
import math
from typing import Optional

'''
两数之和 20240218 xiaojuzi
'''
def twoSum(self, nums: list[int], target: int) -> list[int]:
    hashtable = dict()
    for i, num in enumerate(nums):
        if target - num in hashtable:
            return [hashtable[target - num], i]
        else:
            hashtable[num] = i
    return []


'''
字母异位词分组 20240218 xiaojuzi
'''
def groupAnagrams(self, strs: list[str]) -> list[list[str]]:

    result = collections.defaultdict(list)

    for s in strs:
        key = ''.join(sorted(s))
        result[key].append(s)

    return list(result.values())

'''
最长连续序列 20240218 xiaojuzi
'''
def longestConsecutive(self, nums: list[int]) -> int:
    # 去重 第一次不去重直接超时了- -
    num_set = set(nums)
    max_length = 0

    for num in num_set:
        if num - 1 not in num_set:
            current_num = num
            current_length = 1

            while current_num + 1 in num_set:
                current_num += 1
                current_length += 1

            max_length = max(max_length, current_length)

    return max_length

'''
移动零 20240218 xiaojuzi
'''
def moveZeroes(self, nums: list[int]) -> None:
    i = 0
    for num in nums:
        if num != 0:
            nums[i] = num
            i += 1
    for j in range(i, len(nums)):
        nums[j] = 0

'''
盛最多水的容器 20240218 xiaojuzi
'''
def maxArea(self, height: list[int]) -> int:
    max_area = 0
    left = 0
    right = len(height) - 1

    while left < right:
        current_area = (right - left) * min(height[left], height[right])
        max_area = max(max_area, current_area)
        if height[left] < height[right]:
            left += 1
        else:
            right -= 1

    return max_area

'''
三数之和 20240218 xiaojuzi
'''
def threeSum(self, nums: list[int]) -> list[list[int]]:

    nums.sort()
    result = []
    for i in range(len(nums) - 2):
        #跳过重复元素
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        left = i + 1
        right = len(nums) - 1
        while left < right:
            total = nums[i] + nums[left] + nums[right]
            if total == 0:
                result.append([nums[i], nums[left], nums[right]])
                while left < right and nums[left] == nums[left + 1]:
                    left += 1
                while left < right and nums[right] == nums[right - 1]:
                    right -= 1

                left += 1
                right -= 1

            elif total < 0:
                left += 1
            else:
                right -= 1

    return result


'''
接雨水 20240218 xiaojuzi
'''
def trap(self, height: list[int]) -> int:

    if not height:
        return 0

    n = len(height)
    left, right = 0, n - 1
    left_max, right_max = height[left], height[right]
    water = 0

    while left < right:
        left_max = max(left_max, height[left])
        right_max = max(right_max, height[right])

        if left_max < right_max:
            water += left_max - height[left]
            left += 1
        else:
            water += right_max - height[right]
            right -= 1

    return water

'''
无重复字符的最长子串 20240218 xiaojuzi
'''
def lengthOfLongestSubstring(self, s: str) -> int:

    n = len(s)
    if n == 0:
        return 0

    char_index_map = {}  # 用于记录字符的索引位置
    max_length = 0
    start = 0
    for end,num in enumerate(s):
        if num in char_index_map:
            # 如果当前字符在窗口内已经出现过，更新起始位置
            start = max(start, char_index_map[num] + 1)

        # 更新当前字符的最新位置
        char_index_map[num] = end
        max_length = max(max_length, end - start + 1)

    return max_length


'''
找到字符串中所有字母异位词 20240219 xiaojuzi
'''
def findAnagrams(self, s: str, p: str) -> list[int]:

    result = []
    #统计p中的字符个数
    p_count = collections.defaultdict(int)
    #记录窗口中的字符个数
    window = collections.defaultdict(int)
    required = len(p)
    left, right = 0, 0

    for char in p:
        p_count[char] += 1
    #移动窗口右边界
    while right < len(s):
        char = s[right]
        if char in p_count:
            window[char] += 1
            if window[char] <= p_count[char]:
                required -= 1

        while required == 0:
            if right - left + 1 == len(p):
                result.append(left)

            left_char = s[left]
            if left_char in p_count:
                window[left_char] -= 1
                if window[left_char] < p_count[left_char]:
                    required += 1

            left += 1

        right += 1

    return result

'''
和为 K 的子数组 20240223 xiaojuzi
'''
def subarraySum(self, nums: list[int], k: int) -> int:

    count = 0

    prefix_sum = 0
    # 初始化前缀和为0的个数为1
    prefix_sum_count = {0: 1}

    for num in nums:
        prefix_sum += num
        # 更新count，加上之前出现的前缀和为prefix_sum - k的个数
        count += prefix_sum_count.get(prefix_sum - k, 0)
        # 更新当前前缀和的个数
        prefix_sum_count[prefix_sum] = prefix_sum_count.get(prefix_sum, 0) + 1

    return count

'''
滑动窗口最大值 20240223 xiaojuzi
'''
def maxSlidingWindow(self, nums: list[int], k: int) -> list[int]:

    if not nums:
        return []

    result = []
    #创建双端队列
    window = collections.deque()

    for i, num in enumerate(nums):
        # 移除不在窗口内的元素
        if window and window[0] < i - k + 1:
            window.popleft()

        # 移除比当前元素小的元素
        while window and nums[window[-1]] < num:
            window.pop()

        window.append(i)

        # 当窗口大小达到k时，记录当前窗口的最大值
        if i >= k - 1:
            result.append(nums[window[0]])

    return result


'''
最小覆盖子串 20240223 xiaojuzi
'''
def minWindow(self, s: str, t: str) -> str:

    if not s or not t:
        return ""

    t_freq = collections.Counter(t)
    required_chars = len(t_freq)

    left = 0
    right = 0
    formed = 0
    window_freq = {}

    ans = float('inf'), None, None

    while right < len(s):
        char = s[right]
        window_freq[char] = window_freq.get(char, 0) + 1

        if char in t_freq and window_freq[char] == t_freq[char]:
            formed += 1

        while formed == required_chars and left <= right:
            if right - left + 1 < ans[0]:
                ans = (right - left + 1, left, right)

            char = s[left]
            window_freq[char] -= 1
            if char in t_freq and window_freq[char] < t_freq[char]:
                formed -= 1

            left += 1

        right += 1

    return "" if ans[0] == float('inf') else s[ans[1]:ans[2] + 1]

'''
最大子数组和
'''
def maxSubArray(self, nums: list[int]) -> int:

    if not nums:
        return 0

    dp = [0] * len(nums)
    dp[0] = nums[0]
    max_sum = nums[0]

    for i in range(1, len(nums)):
        dp[i] = max(nums[i], dp[i - 1] + nums[i])
        max_sum = max(max_sum, dp[i])

    return max_sum

'''
合并区间
'''
def merge(self, intervals: list[list[int]]) -> list[list[int]]:

    if not intervals:
        return []

    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]

    for i in range(1, len(intervals)):
        if intervals[i][0] <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], intervals[i][1])
        else:
            merged.append(intervals[i])

    return merged

'''
轮转数组
'''
def rotate(self, nums: list[int], k: int) -> None:

    n = len(nums)
    k = k % n  # 处理k大于数组长度的情况

    def reverse(arr, start, end):
        while start < end:
            arr[start], arr[end] = arr[end], arr[start]
            start += 1
            end -= 1

    reverse(nums, 0, n - 1)
    reverse(nums, 0, k - 1)
    reverse(nums, k, n - 1)

'''
除自身以外数组的乘积 
'''
def productExceptSelf(self, nums: list[int]) -> list[int]:
    n = len(nums)
    answer = [1] * n

    # 计算每个元素左侧所有元素的乘积
    left_product = 1
    for i in range(n):
        answer[i] *= left_product
        left_product *= nums[i]

    # 计算每个元素右侧所有元素的乘积，并与左侧乘积相乘
    right_product = 1
    for i in range(n - 1, -1, -1):
        answer[i] *= right_product
        right_product *= nums[i]

    return answer

'''
缺失的第一个正数 
'''
def firstMissingPositive(self, nums: list[int]) -> int:

    n = len(nums)

    # 将每个正整数调整到正确的位置上
    for i in range(n):
        while 1 <= nums[i] <= n and nums[nums[i] - 1] != nums[i]:
            temp = nums[nums[i] - 1]
            nums[nums[i] - 1] = nums[i]
            nums[i] = temp

    # 再次遍历找出第一个缺失的正整数
    for i in range(n):
        if nums[i] != i + 1:
            return i + 1

    return n + 1

'''
矩阵置零
'''
def setZeroes(self, matrix: list[list[int]]) -> None:

    row = len(matrix)
    col = len(matrix[0])
    row_zero = set()
    col_zero = set()
    for i in range(row):
        for j in range(col):
            if matrix[i][j] == 0:
                row_zero.add(i)
                col_zero.add(j)
    for i in range(row):
        for j in range(col):
            if i in row_zero or j in col_zero:
                matrix[i][j] = 0


'''
螺旋矩阵
'''
def spiralOrder(self, matrix: list[list[int]]) -> list[int]:

    if not matrix:
        return []

    rows, cols = len(matrix), len(matrix[0])
    top, bottom, left, right = 0, rows - 1, 0, cols - 1
    result = []

    while True:
        # 从左到右
        for j in range(left, right + 1):
            result.append(matrix[top][j])
        top += 1

        if top > bottom:
            break

        # 从上到下
        for i in range(top, bottom + 1):
            result.append(matrix[i][right])
        right -= 1

        if left > right:
            break

        # 从右到左
        for j in range(right, left - 1, -1):
            result.append(matrix[bottom][j])
        bottom -= 1

        if top > bottom:
            break

        # 从下到上
        for i in range(bottom, top - 1, -1):
            result.append(matrix[i][left])
        left += 1

        if left > right:
            break

    return result

'''
旋转图像
'''
def rotate(self, matrix: list[list[int]]) -> None:

    n = len(matrix)

    # 转置矩阵
    for i in range(n):
        for j in range(i, n):
            temp = matrix[i][j]
            matrix[i][j] = matrix[j][i]
            matrix[j][i] = temp

    # 翻转每一行
    for i in range(n):
        matrix[i].reverse()


'''
搜索二维矩阵II
'''
def searchMatrix(self, matrix: list[list[int]], target: int) -> bool:

    if not matrix or not matrix[0]:
        return False

    rows, cols = len(matrix), len(matrix[0])
    row, col = 0, cols - 1

    while row < rows and col >= 0:
        if matrix[row][col] == target:
            return True
        elif matrix[row][col] < target:
            row += 1
        else:
            col -= 1

    return False


class ListNode:
    def __init__(self, x):
        self.val = x
        self.next = None
'''
相交链表
'''
def getIntersectionNode(self, headA: ListNode, headB: ListNode) -> ListNode:

    if not headA or not headB:
        return None

    p1, p2 = headA, headB

    while p1 != p2:
        p1 = p1.next if p1 else headB
        p2 = p2.next if p2 else headA

    return p1


'''
反转链表
'''
def reverseList(self, head: Optional[ListNode]) -> Optional[ListNode]:

    if not head or not head.next:
        return head

    cur, pre = head, None
    while cur:
        tmp = cur.next  # 暂存后继节点 cur.next
        cur.next = pre  # 修改 next 引用指向
        pre = cur  # pre 暂存 cur
        cur = tmp  # cur 访问下一节点
    return pre

'''
回文链表
'''
def isPalindrome(self, head: Optional[ListNode]) -> bool:

    result = []
    cur = head
    while cur is not None:
        result.append(cur.val)
        cur = cur.next

    return result == result[::-1]


'''
环形链表
'''
def hasCycle(self, head: Optional[ListNode]) -> bool:

    if not head or not head.next:
        return False

    slow = head
    fast = head.next

    while slow != fast:
        if not fast or not fast.next:
            return False
        slow = slow.next
        fast = fast.next.next

    return True


'''
环形链表II
'''
def detectCycle(self, head: Optional[ListNode]) -> Optional[ListNode]:

    if not head or not head.next:
        return None

    slow = head
    fast = head

    while True:
        if not fast or not fast.next:
            return None
        slow = slow.next
        fast = fast.next.next

        if slow == fast:
            break

    slow = head
    while slow != fast:
        slow = slow.next
        fast = fast.next

    return slow

'''
合并两个有序链表
'''
def mergeTwoLists(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:

    if not l1:
        return l2
    if not l2:
        return l1

    if l1.val < l2.val:
        l1.next = mergeTwoLists(l1.next, l2)
        return l1
    else:
        l2.next = mergeTwoLists(l1, l2.next)
        return l2

'''
两数相加
'''
def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:

    result = ListNode(0)
    current = result
    carry = 0

    while l1 or l2:
        x = l1.val if l1 else 0
        y = l2.val if l2 else 0

        total = x + y + carry
        carry = total // 10

        current.next = ListNode(total % 10)
        current = current.next

        if l1:
            l1 = l1.next
        if l2:
            l2 = l2.next

    if carry > 0:
        current.next = ListNode(carry)

    return result.next

'''
删除链表的倒数第N个结点
'''
def removeNthFromEnd(self, head: Optional[ListNode], n: int) -> Optional[ListNode]:

    dummy = ListNode(0)
    dummy.next = head
    fast = dummy
    slow = dummy

    # 让 fast 先向前移动 n+1 步
    for _ in range(n + 1):
        fast = fast.next

    # 同时移动 fast 和 slow
    while fast is not None:
        fast = fast.next
        slow = slow.next

    # 删除倒数第 n 个节点
    slow.next = slow.next.next

    return dummy.next


'''
两两交换链表中的节点
'''
def swapPairs(self, head: Optional[ListNode]) -> Optional[ListNode]:

        if not head or not head.next:
            return head

        # 交换当前节点和下一个节点
        next_node = head.next
        head.next = swapPairs(next_node.next)
        next_node.next = head

        return next_node


'''
K个一组翻转链表
'''
def reverseKGroup(self, head: Optional[ListNode], k: int) -> Optional[ListNode]:
    def reverseLinkedList(head, k):
        count = 0
        curr = head
        while curr and count < k:
            curr = curr.next
            count += 1
        if count == k:
            reversed_head = reverseLinkedList(curr, k)
            while count > 0:
                next_node = head.next
                head.next = reversed_head
                reversed_head = head
                head = next_node
                count -= 1
            head = reversed_head

        return head

    return reverseLinkedList(head, k)


class Node:
    def __init__(self, x: int, next: 'Node' = None, random: 'Node' = None):
        self.val = int(x)
        self.next = next
        self.random = random
'''
随机链表的复制
'''
def copyRandomList(self, head: Optional[Node]) -> Optional[Node]:
    if not head:
        return None

    # 创建哈希表用于存储原节点和新节点的对应关系
    result_map = {}

    # 第一次遍历，复制节点并存储到哈希表
    curr = head
    while curr:
        result_map[curr] = Node(curr.val)
        curr = curr.next

    # 第二次遍历，处理新节点的指针关系
    curr = head
    while curr:
        if curr.next:
            result_map[curr].next = result_map[curr.next]
        if curr.random:
            result_map[curr].random = result_map[curr.random]
        curr = curr.next

    return result_map[head]


'''
排序链表
'''
def sortList(self, head: Optional[ListNode]) -> Optional[ListNode]:
    if not head or not head.next:
        return head

    def getMiddle(head):
        slow = head
        fast = head

        while fast.next and fast.next.next:
            slow = slow.next
            fast = fast.next.next

        return slow

    def merge(left, right):
        dummy = ListNode(0)
        current = dummy

        while left and right:
            if left.val < right.val:
                current.next = left
                left = left.next
            else:
                current.next = right
                right = right.next
            current = current.next

        current.next = left if left else right

        return dummy.next

    # 获取链表中点，将链表分为两部分
    mid = getMiddle(head)
    left = head
    right = mid.next
    mid.next = None

    # 递归地对左右两部分链表进行排序
    left_sorted = sortList(left)
    right_sorted = sortList(right)

    # 合并两个已排序的链表
    return merge(left_sorted, right_sorted)


'''
合并K个升序链表
'''

def mergeKLists(self, lists: list[Optional[ListNode]]) -> Optional[ListNode]:

    setattr(ListNode, "__lt__", lambda a, b: a.val < b.val)
    heap = []
    for l in lists:
        if l:
            heapq.heappush(heap, (l.val, l))  # 将节点的值和节点本身存入堆中

    dummy = ListNode(0)
    current = dummy

    while heap:
        val, node = heapq.heappop(heap)  # 从堆中取出节点的值和节点本身
        current.next = node
        current = current.next
        if node.next:
            heapq.heappush(heap, (node.next.val, node.next))  # 将下一个节点的值和节点本身存入堆中

    return dummy.next


'''
LRU缓存
'''
class ListNode:
    def __init__(self, key=0, val=0):
        self.key = key
        self.val = val
        self.prev = None
        self.next = None


class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}
        self.head = ListNode()
        self.tail = ListNode()
        self.head.next = self.tail
        self.tail.prev = self.head

    def get(self, key):
        if key in self.cache:
            node = self.cache[key]
            self._remove(node)
            self._add(node)
            return node.val
        return -1

    def put(self, key, value):
        if key in self.cache:
            self._remove(self.cache[key])
        node = ListNode(key, value)
        self.cache[key] = node
        self._add(node)

        if len(self.cache) > self.capacity:
            node_to_remove = self.head.next
            self._remove(node_to_remove)
            del self.cache[node_to_remove.key]

    def _add(self, node):
        prev_node = self.tail.prev
        prev_node.next = node
        node.prev = prev_node
        node.next = self.tail
        self.tail.prev = node

    def _remove(self, node):
        prev_node = node.prev
        next_node = node.next
        prev_node.next = next_node
        next_node.prev = prev_node



'''
二叉树的中序遍历
'''

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
def inorderTraversal(self, root: Optional[TreeNode]) -> list[int]:
    def inorder(node,result):
        if not node:
            return []
        inorder(node.left,result)
        result.append(node.val)
        inorder(node.right,result)

    result = []
    inorder(root,result)

    return result


'''
二叉树的最大深度
'''
def maxDepth(self, root: Optional[TreeNode]) -> int:
    if not root:
        return 0

    left_depth = maxDepth(root.left)
    right_depth = maxDepth(root.right)

    return max(left_depth, right_depth) + 1

'''
翻转二叉树
'''
def invertTree(self, root: Optional[TreeNode]) -> Optional[TreeNode]:
    if not root:
        return None
    #交换左右子树
    root.left, root.right = root.right, root.left
    invertTree(root.left)
    invertTree(root.right)

    return root

'''
对称二叉树
'''
def isSymmetric(self, root: Optional[TreeNode]) -> bool:
    def isMirror(left, right):
        if not left and not right:
            return True
        if not left or not right:
            return False
        return (left.val == right.val) and isMirror(left.left, right.right) and isMirror(left.right, right.left)

    if not root:
        return True
    return isMirror(root.left, root.right)

'''
二叉树的直径
'''

def diameterOfBinaryTree(self, root: Optional[TreeNode]) -> int:

    self.count = 0
    def depth(node):
        if not node:
            return 0
        left_depth = depth(node.left)
        right_depth = depth(node.right)
        self.count = max(self.count, left_depth + right_depth)
        return 1 + max(left_depth, right_depth)

    depth(root)

    return self.count

'''
二叉树的层次遍历
'''
def levelOrder(self, root: Optional[TreeNode]) -> list[list[int]]:
    if not root:
        return []

    queue = collections.deque([root])
    result = []
    while queue:
        level_vales = []
        for _ in range(len(queue)):
            node = queue.popleft()
            level_vales.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        result.append(level_vales)

    return result

'''
将有序数组转换为二叉搜索树
'''
def sortedArrayToBST(self, nums: list[int]) -> Optional[TreeNode]:

    if not nums:
        return None

    mid = len(nums) // 2
    root = TreeNode(nums[mid])

    root.left = sortedArrayToBST(nums[:mid])
    root.right = sortedArrayToBST(nums[mid + 1:])

    return root

'''
验证二叉搜索树
'''
def isValidBST(self, root: Optional[TreeNode]) -> bool:

    def isValid(node, min_val, max_val):
        if not node:
            return True
        if not min_val < node.val < max_val:
            return False

        return isValid(node.left, min_val, node.val) and isValid(node.right, node.val, max_val)

    return isValid(root, float('-inf'), float('inf'))  # 对于根节点，它的上下限为无穷大和无穷小


'''
二叉搜索树中第K小的元素
'''
def kthSmallest(self, root: Optional[TreeNode], k: int) -> int:

    def inorder(node):
        nonlocal k
        if not node:
            return None
        val = inorder(node.left)
        if val is not None:
            return val
        k -= 1
        if k == 0:
            return node.val
        return inorder(node.right)

    return inorder(root)

'''
二叉树的右视图
'''
def rightSideView(self, root: Optional[TreeNode]) -> list[int]:

    if not root:
        return []

    result = []
    queue = collections.deque([root])

    while queue:
        level_size = len(queue)
        for i in range(level_size):
            node = queue.popleft()
            if i == level_size - 1:
                result.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)

    return result


'''
二叉树展开为链表
'''
def flatten(self, root: Optional[TreeNode]) -> None:

    if not root:
        return

    flatten(root.left)
    flatten(root.right)

    temp = root.right
    root.right = root.left
    root.left = None

    while root.right:
        root = root.right

    root.right = temp

'''
从前序与中序遍历序列构造二叉树
'''
def buildTree(self, preorder: list[int], inorder: list[int]) -> Optional[TreeNode]:
    if not preorder or not inorder:
        return None
    #preorder = [3,9,20,15,7], inorder = [9,3,15,20,7]
    root_val = preorder[0]
    root = TreeNode(root_val)

    root_index = inorder.index(root_val)

    root.left = buildTree(preorder[1:1 + root_index], inorder[:root_index])
    root.right = buildTree(preorder[1 + root_index:], inorder[root_index + 1:])

    return root

'''
路径总和III
'''
def pathSum(self, root: Optional[TreeNode], targetSum: int) -> int:
    def dfs(node, target):
        if not node:
            return 0

        count = 0
        if node.val == target:
            count += 1

        count += dfs(node.left, target - node.val)
        count += dfs(node.right, target - node.val)

        return count

    if not root:
        return 0

    return dfs(root, targetSum) + pathSum(root.left, targetSum) + pathSum(root.right, targetSum)


'''
二叉树的最近公共祖先
'''
def lowestCommonAncestor(self, root: Optional[TreeNode], p: Optional[TreeNode], q: Optional[TreeNode]) -> Optional[TreeNode]:

    if not root or root == p or root == q:
        return root

    left = lowestCommonAncestor(root.left, p, q)
    right = lowestCommonAncestor(root.right, p, q)

    if left and right:
        return root
    elif left:
        return left
    else:
        return right



'''
二叉树中的最大路径和
'''
def maxPathSum(self, root: Optional[TreeNode]) -> int:

    self.max_sum = float('-inf')

    def max_path(node):
        if not node:
            return 0

        left_sum = max(max_path(node.left), 0)
        right_sum = max(max_path(node.right), 0)

        # 当前节点作为路径中的根节点时的最大路径和
        current_path_sum = node.val + left_sum + right_sum

        self.max_sum = max(self.max_sum, current_path_sum)

        # 返回当前节点的最大路径和
        return node.val + max(left_sum, right_sum)

    max_path(root)

    return self.max_sum


'''
岛屿数量
'''
def numIslands(self, grid: list[list[str]]) -> int:
    def dfs(grid, i, j):
        if i < 0 or i >= len(grid) or j < 0 or j >= len(grid[0]) or grid[i][j] == '0':
            return
        grid[i][j] = '0'  # 标记当前陆地为已访问
        # 递归访问当前陆地的上下左右四个方向
        dfs(grid, i + 1, j)
        dfs(grid, i - 1, j)
        dfs(grid, i, j + 1)
        dfs(grid, i, j - 1)

    if not grid:
        return 0

    num_islands = 0
    rows, cols = len(grid), len(grid[0])

    for i in range(rows):
        for j in range(cols):
            if grid[i][j] == '1':
                num_islands += 1
                dfs(grid, i, j)

    return num_islands

def numIslands2(grid):
    def bfs(grid, i, j):
        queue = collections.deque([(i, j)])
        grid[i][j] = '0'  # 标记当前陆地为已访问

        while queue:
            x, y = queue.popleft()
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            for dx, dy in directions:
                new_x, new_y = x + dx, y + dy
                if 0 <= new_x < len(grid) and 0 <= new_y < len(grid[0]) and grid[new_x][new_y] == '1':
                    queue.append((new_x, new_y))
                    grid[new_x][new_y] = '0'  # 标记当前陆地为已访问

    if not grid:
        return 0

    num_islands = 0
    rows, cols = len(grid), len(grid[0])

    for i in range(rows):
        for j in range(cols):
            if grid[i][j] == '1':
                num_islands += 1
                bfs(grid, i, j)

    return num_islands

'''
腐烂的橘子
'''
def orangesRotting(self, grid: list[list[int]]) -> int:

    if not grid:
        return 0

    rows, cols = len(grid), len(grid[0])
    fresh_oranges = 0
    rotten_oranges = collections.deque()

    # 统计新鲜橘子的数量，并将腐烂橘子的位置加入队列
    for i in range(rows):
        for j in range(cols):
            if grid[i][j] == 1:
                fresh_oranges += 1
            elif grid[i][j] == 2:
                rotten_oranges.append((i, j))

    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    minutes = 0

    while fresh_oranges > 0 and rotten_oranges:
        minutes += 1
        new_rotten_oranges = collections.deque()

        while rotten_oranges:
            x, y = rotten_oranges.popleft()

            for dx, dy in directions:
                new_x, new_y = x + dx, y + dy
                if 0 <= new_x < rows and 0 <= new_y < cols and grid[new_x][new_y] == 1:
                    grid[new_x][new_y] = 2
                    fresh_oranges -= 1
                    new_rotten_oranges.append((new_x, new_y))

        rotten_oranges = new_rotten_oranges

    return minutes if fresh_oranges == 0 else -1


'''
课程表
'''
def canFinish(self, numCourses: int, prerequisites: list[list[int]]) -> bool:

    graph = collections.defaultdict(list)
    indegree = [0] * numCourses

    # 构建图和入度数组
    for course, pre_course in prerequisites:
        graph[pre_course].append(course)
        indegree[course] += 1

    # 拓扑排序
    queue = [i for i in range(numCourses) if indegree[i] == 0]
    while queue:
        node = queue.pop(0)
        numCourses -= 1
        for neighbor in graph[node]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)

    return numCourses == 0



'''
实现 Trie (前缀树)
'''
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False
class Trie:

    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True


    def search(self, word: str) -> bool:
        node = self._search_prefix(word)
        return node is not None and node.is_end_of_word


    def startsWith(self, prefix: str) -> bool:
        return self._search_prefix(prefix) is not None

    def _search_prefix(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return None
            node = node.children[char]
        return node

'''
全排列
'''
def permute(nums: list[int]) -> list[list[int]]:

    def backtrack(first):
        if first == n-1:
            res.append(list(nums))
            return
        for i in range(first, n):
            nums[first], nums[i] = nums[i], nums[first]
            backtrack(first + 1)
            nums[first], nums[i] = nums[i], nums[first]

    n = len(nums)
    res = []
    backtrack(0)
    return res


'''
子集
'''
def subsets(nums: list[int]) -> list[list[int]]:
    def backtrack(start, path):
        res.append(path[:])
        for i in range(start, len(nums)):
            path.append(nums[i])
            backtrack(i + 1, path)
            path.pop()

    res = []
    backtrack(0, [])
    return res


'''
电话号码的字母组合
'''
def letterCombinations(digits: str) -> list[str]:
    if not digits:
        return []

    phone = {
        '2': ['a', 'b', 'c'],
        '3': ['d', 'e', 'f'],
        '4': ['g', 'h', 'i'],
        '5': ['j', 'k', 'l'],
        '6': ['m', 'n', 'o'],
        '7': ['p', 'q', 'r', 's'],
        '8': ['t', 'u', 'v'],
        '9': ['w', 'x', 'y', 'z']
    }

    def backtrack(index, path):
        if index == len(digits):
            res.append(''.join(path))
            return

        for char in phone[digits[index]]:
            path.append(char)
            backtrack(index + 1, path)
            path.pop()

    res = []
    backtrack(0, [])
    return res

'''
组合总合
'''
def combinationSum(candidates: list[int], target: int) -> list[list[int]]:

    def backtrack(start, path, target):
        if target == 0:
            res.append(path[:])
            return
        if target < 0:
            return

        for i in range(start, len(candidates)):
            path.append(candidates[i])
            backtrack(i, path, target - candidates[i])
            path.pop()

    res = []
    candidates.sort()
    backtrack(0, [], target)
    return res

'''
括号生成
'''
def generateParenthesis(n: int) -> list[str]:

    def backtrack(left, right, path):
        if len(path) == 2 * n:
            res.append("".join(path))
            return
        if left < n:
            path.append('(')
            backtrack(left + 1, right, path)
            path.pop()
        if right < left:
            path.append(')')
            backtrack(left, right + 1, path)
            path.pop()

    res = []
    backtrack(0, 0, [])
    return res

'''
单词搜索
'''
def exist(board: list[list[str]], word: str) -> bool:

    def dfs(i, j, k):
        if not 0 <= i < len(board) or not 0 <= j < len(board[0]) or board[i][j] != word[k]:
            return False
        if k == len(word) - 1:
            return True

        temp, board[i][j] = board[i][j], '/'
        res = dfs(i + 1, j, k + 1) or dfs(i - 1, j, k + 1) or dfs(i, j + 1, k + 1) or dfs(i, j - 1, k + 1)
        board[i][j] = temp
        return res

    for i in range(len(board)):
        for j in range(len(board[0])):
            if dfs(i, j, 0):
                return True
    return False

'''
分割回文串
'''
def partition(s: str) -> list[list[str]]:

    def is_palindromic(s):
        return s == s[::-1]

    def backtrack(start, path):
        if start == len(s):
            result.append(path[:])
            return

        for end in range(start + 1, len(s) + 1):
            # print('start:%s,end:%s,s:%s'%(start,end,s[start:end]))
            if is_palindromic(s[start:end]):
                path.append(s[start:end])
                backtrack(end, path)
                path.pop()

    result = []
    backtrack(0, [])
    return result



'''
N皇后
'''
def NQueens(n: int) -> list[list[str]]:
    '''
    判断在给定行 row 和列 col 上放置皇后是否与已放置的皇后相互攻击。
    通过检查三个方向（列、主对角线和副对角线）是否存在皇后来实现，返回布尔值。
    '''
    def is_not_under_attack(row, col):
        return not (cols[col] or diag1[row + col] or diag2[row - col])

    '''
    在给定行 row 和列 col 上放置皇后，并相应地更新三组标志数组 cols（记录每列是否有皇后）、
    diag1（记录主对角线上是否有皇后）和 diag2（记录副对角线上是否有皇后），将对应位置标记为1表示有皇后。
    '''
    def place_queen(row, col):
        queens[row] = col
        cols[col] = diag1[row + col] = diag2[row - col] = 1

    '''
    移除在给定行 row 和列 col 上的皇后，并将三组标志数组相应位置恢复为0。
    '''
    def remove_queen(row, col):
        cols[col] = diag1[row + col] = diag2[row - col] = 0

    '''
    当成功找到一种皇后放置方案时，将其转化为字符串形式并添加到解决方案列表 solutions 中。
    每一行是一个字符串，由 '.' 和 'Q' 组成，表示棋盘的状态。
    '''
    def add_solution():
        solution = []
        for row, col in enumerate(queens):
            solution.append('.' * col + 'Q' + '.' * (n - col - 1))
        solutions.append(solution)

    def backtrack(row):
        for col in range(n):
            if is_not_under_attack(row, col):
                place_queen(row, col)
                if row + 1 == n:
                    add_solution()
                else:
                    backtrack(row + 1)
                remove_queen(row, col)

    '''
    初始化三个标志数组：cols 用于记录各列是否有皇后，diag1 和 diag2 分别用于记录两条对角线上的皇后情况。
    初始化皇后位置列表 queens 和存储解决方案的列表 solutions。 
    调用回溯函数 backtrack(0) 从第一行开始尝试放置皇后。
    '''
    cols = [0] * n
    diag1 = [0] * (2 * n - 1)
    diag2 = [0] * (2 * n - 1)

    queens = [0] * n
    solutions = []

    backtrack(0)
    return solutions


'''
搜索插入位置
'''
def searchInsert(nums: list[int], target: int) -> int:
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] < target:
            left = mid + 1
        elif nums[mid] > target:
            right = mid - 1
        else:
            return mid

    return left


'''
搜索二维矩阵
'''
def searchMatrix(matrix: list[list[int]], target: int) -> bool:

    if not matrix or not matrix[0]:

        return False

    rows, cols = len(matrix), len(matrix[0])
    row, col = 0, cols - 1

    while row < rows and col >= 0:
        if matrix[row][col] == target:
            return True
        elif matrix[row][col] < target:
            row += 1
        else:
            col -= 1

    return False

'''
在排序数组中查找元素的第一个和最后一个位置
nums = [5,7,7,8,8,10]
target = 8
'''
def searchRange(nums: list[int], target: int) -> list[int]:
    def find_first(nums, target):
        left, right = 0, len(nums) - 1
        while left <= right:
            mid = (right + left) // 2
            if nums[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        return left

    def find_last(nums, target):
        left, right = 0, len(nums) - 1
        while left <= right:
            mid = (right + left) // 2
            if nums[mid] <= target:
                left = mid + 1
            else:
                right = mid - 1
        return right

    start = find_first(nums, target)
    end = find_last(nums, target)

    if start <= end:
        return [start, end]
    else:
        return [-1, -1]

'''
搜索旋转排序数组
'''
def search(nums: list[int], target: int) -> int:

    left, right = 0, len(nums) - 1

    while left <= right:
        mid = (left + right) // 2

        if nums[mid] == target:
            return mid

        if nums[left] <= nums[mid]:  # 左半部分有序
            if nums[left] <= target < nums[mid]:
                right = mid - 1
            else:
                left = mid + 1
        else:  # 右半部分有序
            if nums[mid] < target <= nums[right]:
                left = mid + 1
            else:
                right = mid - 1

    return -1


'''
寻找旋转排序数组中的最小值
'''
def findMin(nums: list[int]) -> int:
    left, right = 0, len(nums) - 1

    while left < right:
        mid = (right + left) // 2

        if nums[mid] < nums[right]:  # 右半部分有序，最小值在左半部分或者就是当前位置
            right = mid
        else:  # 右半部分无序，最小值在右半部分
            left = mid + 1

    return nums[left]

'''
寻找两个正序数组的中位数
'''
def findMedianSortedArrays(nums1: list[int], nums2: list[int]) -> float:

    if len(nums1) > len(nums2):
        return findMedianSortedArrays(nums2, nums1)

    infinty = 2 ** 40
    m, n = len(nums1), len(nums2)
    left, right = 0, m
    # median1：前一部分的最大值
    # median2：后一部分的最小值
    median1, median2 = 0, 0

    while left <= right:
        # 前一部分包含 nums1[0 .. i-1] 和 nums2[0 .. j-1]
        # // 后一部分包含 nums1[i .. m-1] 和 nums2[j .. n-1]
        i = (left + right) // 2
        j = (m + n + 1) // 2 - i

        # nums_im1, nums_i, nums_jm1, nums_j 分别表示 nums1[i-1], nums1[i], nums2[j-1], nums2[j]
        nums_im1 = (-infinty if i == 0 else nums1[i - 1])
        nums_i = (infinty if i == m else nums1[i])
        nums_jm1 = (-infinty if j == 0 else nums2[j - 1])
        nums_j = (infinty if j == n else nums2[j])

        if nums_im1 <= nums_j:
            median1, median2 = max(nums_im1, nums_jm1), min(nums_i, nums_j)
            left = i + 1
        else:
            right = i - 1

    return (median1 + median2) / 2 if (m + n) % 2 == 0 else median1


'''
有效的括号 
'''
def isValid(s: str) -> bool:
    stack = []
    mapping = {')': '(', '}': '{', ']': '['}

    for char in s:
        if char in mapping.values():
            stack.append(char)
        elif char in mapping:
            if not stack or mapping[char] != stack.pop():
                return False

    return not stack


'''
最小栈
'''
class MinStack:

    def __init__(self):
        self.stack = []
        self.min_stack = []

    def push(self, val: int) -> None:
        self.stack.append(val)
        if not self.min_stack or val <= self.min_stack[-1]:
            self.min_stack.append(val)

    def pop(self) -> None:
        if self.stack[-1] == self.min_stack[-1]:
            self.min_stack.pop()
        self.stack.pop()

    def top(self) -> int:
        return self.stack[-1]

    def getMin(self) -> int:
        return self.min_stack[-1]

'''
字符串解码
'''
def decodeString(s: str) -> str:
    stack = []
    current_str = ""
    current_num = 0

    for char in s:
        if char.isdigit():
            current_num = current_num * 10 + int(char)
        elif char.isalpha():
            current_str += char
        elif char == "[":
            stack.append(current_str)
            stack.append(current_num)
            current_str = ""
            current_num = 0
        elif char == "]":
            num = stack.pop()
            prev_str = stack.pop()
            current_str = prev_str + num * current_str

    return current_str

'''
每日温度
'''
def dailyTemperatures(temperatures: list[int]) -> list[int]:

    n = len(temperatures)
    stack = []
    answer = [0] * n

    for i in range(n):
        while stack and temperatures[i] > temperatures[stack[-1]]:
            top_index = stack.pop()
            answer[top_index] = i - top_index

        stack.append(i)

    return answer

'''
柱状图中最大的矩形
'''
def largestRectangleArea(heights: list[int]) -> int:
    heights.append(0)  # 添加高度为0的柱子
    n = len(heights)
    stack = []
    max_area = 0

    for i in range(n):
        while stack and heights[i] < heights[stack[-1]]:
            top = stack.pop()
            width = i if not stack else i - stack[-1] - 1
            max_area = max(max_area, width * heights[top])

        stack.append(i)

    return max_area

'''
数组中的第K个最大元素
'''
def findKthLargest(nums: list[int], k: int) -> int:
    heap = []
    for num in nums:
        heapq.heappush(heap, num)
        if len(heap) > k:
            heapq.heappop(heap)

    return heap[0]

'''
前K个高频元素
'''
def topKFrequent(nums: list[int], k: int) -> list[int]:
    # 使用 Counter 统计每个元素的频率
    counter = collections.Counter(nums)

    # 对字典按值进行排序，获取前 k 高频率的元素
    sorted_counter = sorted(counter.items(), key=lambda x: x[1], reverse=True)

    # 获取前 k 高频率的元素
    result = [x[0] for x in sorted_counter[:k]]

    return result


'''
数据流的中位数
'''

class MedianFinder:

    def __init__(self):
        # 最大堆，存储较小一半的元素
        self.max_heap = []
        # 最小堆，存储较大一半的元素
        self.min_heap = []

    def addNum(self, num: int) -> None:
        # 先将元素插入最大堆
        heapq.heappush(self.max_heap, -num)

        # 将最大堆的最大值弹出并插入最小堆
        heapq.heappush(self.min_heap, -heapq.heappop(self.max_heap))

        # 如果最小堆的大小比最大堆大，将最小堆的最小值弹出并插入最大堆
        if len(self.min_heap) > len(self.max_heap):
            heapq.heappush(self.max_heap, -heapq.heappop(self.min_heap))

    def findMedian(self) -> float:
        if len(self.max_heap) == len(self.min_heap):
            return (self.min_heap[0] - self.max_heap[0]) / 2
        else:
            return -self.max_heap[0]


'''
买卖股票的最佳时机
'''
def maxProfit(prices: list[int]) -> int:
    min_price = prices[0]
    max_profit = 0

    for price in prices:
        if price < min_price:
            min_price = price
        else:
            max_profit = max(max_profit,price - min_price)

    return max_profit



'''
跳跃游戏
'''
def canJump(nums: list[int]) -> bool:
    last_position = len(nums) - 1

    for i in range(len(nums) - 1, -1, -1):
        #计算当前位置能够跳跃的最远距离
        if i + nums[i] >= last_position:
            last_position = i

    return last_position == 0


'''
跳跃游戏II
'''
def jump(nums: list[int]) -> int:
    n = len(nums)
    jumps = 0
    curr_end = 0
    curr_farthest = 0

    for i in range(n - 1):
        curr_farthest = max(curr_farthest, i + nums[i])
        if i == curr_end:
            jumps += 1
            curr_end = curr_farthest
            if curr_end >= n - 1:
                return jumps

    return jumps


'''
划分字母区间
'''
def partitionLabels(s: str) -> list[int]:

    last_occurrence = {char: i for i, char in enumerate(s)}

    result = []
    start = 0
    end = 0

    for i, char in enumerate(s):
        end = max(end, last_occurrence[char])
        if i == end:
            result.append(end - start + 1)
            start = end + 1

    return result

'''
爬楼梯
'''
def climbStairs(n: int) -> int:
    if n == 1:
        return 1

    dp = [0] * (n + 1)
    dp[0] = dp[1] = 1

    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]

    return dp[n]

'''
杨辉三角
'''
def generate(numRows: int) -> list[list[int]]:

    result = []

    for i in range(numRows):
        row = [1] * (i + 1)
        if i > 1:
            for j in range(1, i):
                row[j] = result[i - 1][j-1] + row[i - 1][j]
        result.append(row)

    return result

'''
打家劫舍
'''
def rob(nums: list[int]) -> int:

    if not nums:
        return 0

    if len(nums) == 1:
        return nums[0]

    # 初始化动态规划数组
    dp = [0] * len(nums)
    dp[0] = nums[0]
    dp[1] = max(nums[0], nums[1])

    # 动态规划过程
    for i in range(2, len(nums)):
        dp[i] = max(dp[i - 1], dp[i - 2] + nums[i])

    return dp[-1]

'''
完全平方数
'''
def numSquares(n: int) -> int:

    dp = [float('inf')] * (n + 1)
    dp[0] = 0

    for i in range(1, n + 1):
        for j in range(1, int(math.sqrt(i)) + 1):
            dp[i] = min(dp[i], dp[i - j * j] + 1)

    return dp[n]

'''
零钱兑换
'''
def coinChange(coins: list[int], amount: int) -> int:

    dp = [float('inf')] * (amount + 1)

    dp[0] = 0

    for i in range(1, amount + 1):
        for coin in coins:
            if i - coin >= 0:
                dp[i] = min(dp[i], dp[i - coin] + 1)

    return dp[amount] if dp[amount] != float('inf') else -1


'''
单词拆分
'''
def  wordBreak(s: str, wordDict: list[str]) -> bool:

    n = len(s)
    dp = [False] * (n + 1)
    dp[0] = True

    wordSet = set(wordDict)

    for i in range(1, n + 1):
        for j in range(i):
            if dp[j] and s[j:i] in wordSet:
                dp[i] = True
                break

    return dp[n]


'''
最长递增子序列
'''
def  lengthOfLIS(nums: list[int]) -> int:
    if not nums:
        return 0

    n = len(nums)
    dp = [1] * n

    for i in range(1, n):
        for j in range(i):
            if nums[i] > nums[j]:
                dp[i] = max(dp[i], dp[j] + 1)

    return max(dp)


'''
乘积最大子数组
'''
def maxmaxProduct(nums: list[int]) -> int:
    if not nums:
        return 0
    max_num, min_num, result = nums[0], nums[0], nums[0]
    for i in range(1, len(nums)):
        if nums[i] < 0:
            max_num, min_num = min_num, max_num

        max_num = max(nums[i], max_num * nums[i])
        min_num = min(nums[i], min_num * nums[i])

        result = max(max_num, result)

    return result


'''
分割等和子集
'''
def canPartition(nums: list[int]) -> bool:
    total_sum = sum(nums)
    if total_sum % 2 != 0:
        return False

    target = total_sum // 2
    n = len(nums)
    dp = [[False for _ in range(target + 1)] for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = True

    for i in range(1, n + 1):
        for j in range(1, target + 1):
            if j < nums[i - 1]:
                dp[i][j] = dp[i - 1][j]
            else:
                dp[i][j] = dp[i - 1][j] or dp[i - 1][j - nums[i - 1]]

    return dp[n][target]



'''
最长有效括号
'''
def  longestlongestValidParentheses(s: str) -> int:

    stack = []
    stack.append(-1)
    max_length = 0

    for i in range(len(s)):
        if s[i] == '(':
            stack.append(i)
        else:
            stack.pop()
            if len(stack) == 0:
                stack.append(i)
            else:
                max_length = max(max_length, i - stack[-1])

    return max_length

'''
不同路径
'''
def uniquePaths(m: int, n: int) -> int:
    dp = [[1] * n for _ in range(m)]

    for i in range(1, m):
        for j in range(1, n):
            dp[i][j] = dp[i - 1][j] + dp[i][j - 1]

    return dp[m - 1][n - 1]



'''
最小路径和
'''
def  minminPathSum(grid: list[list[int]]) -> int:
    m, n = len(grid), len(grid[0])

    for i in range(1, m):
        grid[i][0] += grid[i - 1][0]

    for j in range(1, n):
        grid[0][j] += grid[0][j - 1]

    for i in range(1, m):
        for j in range(1, n):
            grid[i][j] += min(grid[i - 1][j], grid[i][j - 1])

    return grid[m - 1][n - 1]


'''
最小回文字符串
'''
def  minminCut(s: str) -> int:
    n = len(s)
    dp = [[False] * n for _ in range(n)]
    start = 0
    max_length = 1

    # 单个字符一定是回文串
    for i in range(n):
        dp[i][i] = True

    # 遍历所有可能的子串长度和起始索引
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            if length == 2 and s[i] == s[j]:
                dp[i][j] = True
            elif s[i] == s[j] and dp[i + 1][j - 1]:
                dp[i][j] = True
            if dp[i][j] and length > max_length:
                start = i
                max_length = length

    return s[start:start + max_length]

'''
最长公共子序列
'''
def  longestCommonSubsequence(text1: str, text2: str) -> int:

    m, n = len(text1), len(text2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i - 1] == text2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    return dp[m][n]

'''
编辑距离
'''
def minminDistance(word1: str, word2: str) -> int:
    m, n = len(word1), len(word2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i

    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if word1[i - 1] == word2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]) + 1

    return dp[m][n]


'''
只出现一次的数字
'''
def singleNumber(nums: list[int]) -> int:
    result = 0
    for num in nums:
        result ^= num
    return result

'''
多数元素
'''
def majorityElement(nums: list[int]) -> int:
    candidate = None
    count = 0

    for num in nums:
        if count == 0:
            candidate = num
        count += 1 if num == candidate else -1

    return candidate


'''
颜色分类
'''
def sortColors(nums: list[int]) -> None:
    left, right, curr = 0, len(nums) - 1, 0

    while curr <= right:
        if nums[curr] == 0:
            nums[curr], nums[left] = nums[left], nums[curr]
            curr += 1
            left += 1
        elif nums[curr] == 2:
            nums[curr], nums[right] = nums[right], nums[curr]
            right -= 1
        else:
            curr += 1


'''
下一个排列
'''
def nextPermutation(nums: list[int]) -> None:

    n = len(nums)
    i = n - 2

    # 找到第一个降序的位置i
    while i >= 0 and nums[i] >= nums[i + 1]:
        i -= 1

    if i >= 0:
        j = n - 1
        # 找到大于nums[i]的最小元素
        while nums[j] <= nums[i]:
            j -= 1
        nums[i], nums[j] = nums[j], nums[i]

    # 将位置i右侧的元素按升序排列
    left, right = i + 1, n - 1
    while left < right:
        nums[left], nums[right] = nums[right], nums[left]
        left += 1
        right -= 1


'''
寻找重复数
'''
def  findDuplicate(nums: list[int]) -> int:
    slow = nums[0]
    fast = nums[0]

    while True:
        slow = nums[slow]
        fast = nums[nums[fast]]

        if slow == fast:
            break

    fast = nums[0]
    while slow != fast:
        slow = nums[slow]
        fast = nums[fast]

    return slow

'''
鸡蛋掉落
'''
def eggDrop(eggs, floors):

    dp = [[0] * (floors + 1) for _ in range(eggs + 1)]

    for j in range(1, floors + 1):
        dp[1][j] = j

    for i in range(2, eggs + 1):
        for j in range(1, floors + 1):
            dp[i][j] = float('inf')
            for k in range(1, j + 1):
                dp[i][j] = min(dp[i][j], max(dp[i-1][k-1], dp[i][j-k]) + 1)

    return dp[eggs][floors]