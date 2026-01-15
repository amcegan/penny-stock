from typing import List


class Solution:
    from typing import List
    def lengthOfLongestSubstring(self, s: str) -> int:
        longest = 0
        count = 0
        mySet = set()

        for i, ele in enumerate(s):
            if ele in mySet:
                mySet.clear()
                if count > longest:
                    longest = count
                count = 0
            else:
                mySet.add(ele)
                count += 1

        return longest

    def lP(self):
        strs = ["flower","flow","flight"]
        prefix = strs[0]

        
        for i, str in enumerate(strs):
            
            if i == 0:
                continue

            recurs = min(len(prefix), len(str))

            while recurs > 0:
                recurs -= 1
                if prefix[:recurs] == str[:recurs]:
                    prefix = prefix[:recurs]
                    break
        print (prefix)

    def removeDups(self):
        nums = [1,1,2,2,3,3,4,4,5]
        k = 0
        result = []
        for i, num in enumerate(nums):
            if i == 0:  # rethink edge cases; should we use i
                result.append(num)
                k = 1
                continue

            if result[len(result)-1] == num:
                continue
            else:
                result.append(num)
                k += 1
        print (result)
        return k
    

    def maxArea(self):
        # find the min height of two lines and multiply by the distance between them
        height = [1,8,6,2,5,4,8,3,7]
        vol = 0
        print ('len ', len(height))
        for i, n in enumerate(height):
            j = i + 1
            while j < len(height):
                print (i, j)
                if (j-i) * min(height[j], height[i]) > vol:
                    vol = (j-i)*height[j]
                    # print j - i, height[j], vol
                    print (j, '-', i, '*', height[j], vol)
                    print (vol)
                j = j + 1
        return vol
    


    def maxAreaOpt(self):
        height = [1,8,6,2,5,4,8,3,7]
        left = 0
        right = len(height) - 1
        vol = 0

        while left < right:
            h = min(height[left], height[right])
            vol = max(vol, h * (right - left))

            if height[left] < height[right]:
                left += 1
            else:
                right -= 1

        return vol


    def removeDuplicates(self) -> int:
        # Input: 
        nums = [0,0,1,1,1,2,2,3,3,4]
        # Output: 2, nums = [1,2,_]
        n = 1
        p = 0
        while n < len(nums):
            if nums[p] == nums[n]:
                p = p
            else:
                nums[p + 1] = nums[n]
                p = p + 1
            n = n + 1
        print (nums)
        return p

    def search(self) -> int:
        nums = [-1,0,3,5,9,12]
        target = 9

        if target < nums[0] or target > nums[len(nums) - 1]:
            return -1

        if target < nums[0] or target > nums[len(nums) - 1]:
            return -1

        left = 0
        right = len(nums) - 1

        while left <= right:
            center = (left + right) // 2
            print (left, right, center)
            if target > nums[center]:
                left = center

            if target < nums[center]:
                right = center

            if target == nums[center]:
                return center

        return -1 

#Title: N-Repeated Element in Size 2N Array 
# You are given an integer array nums with the following properties: 
# nums.length == 2 * n. 
# nums contains n + 1 unique elements. 
# Exactly one element of nums is repeated n times. 
# Return the element that is repeated n times.
# Input: nums = [5,1,5,2,5,3,5,4] Output: 5
    def repeatedNTimes(self) -> int:
        nums = [5,1,5,2,5,3,5,4]
        seen = set()
        for x in nums:
            if x in seen:
                return x
            seen.add(x)
        return -1  # should never happen given constraints

    def r2(self) -> int:
        nums = [1,2,3,4,5,5,5,5]
        m = len(nums)
        for k in (1, 2, 3):
            for i in range(m - k):
                if nums[i] == nums[i + k]:
                    return nums[i]
        return -1
    


    


            