# coding = utf-8

# 基于用户的协同过滤推荐算法实现
import random



from app.models import Rating
import numpy as np


class UserBasedCF():
    # 初始化相关参数
    def __init__(self):
        # 找到与目标用户兴趣相似的20个用户，为其推荐10部新闻
        self.n_sim_user = 20
        self.n_rec_news = 10

        # 将数据集划分为训练集和测试集
        self.trainSet = {}
        self.testSet = {}

        # 用户相似度矩阵
        self.user_sim_matrix = {}
        self.news_count = 0

        print('Similar user number = %d' % self.n_sim_user)
        print('Recommneded news number = %d' % self.n_rec_news)

    # 读取“用户-新闻”数据
    def get_dataset(self, ratings, pivot=0.75):
        trainSet_len = 0
        testSet_len = 0
        for rating in ratings:
            user = rating.userid
            news = rating.newsid
            rating = rating.rating
            if random.random() < pivot:
                self.trainSet.setdefault(user, {})
                self.trainSet[user][news] = int(rating)
                trainSet_len += 1
            else:
                self.testSet.setdefault(user, {})
                self.testSet[user][news] = int(rating)
                testSet_len += 1
        print('Split trainingSet and testSet success!')
        print('TrainSet = %s' % trainSet_len)
        print('TestSet = %s' % testSet_len)

    # 计算用户之间的相似度
    def calc_user_sim(self):
        # 统计每个新闻的流行程度
        print("统计每个新闻的流行程度.........")
        news_popular = {}
        for user, news in self.trainSet.items():
            for news in news:
                if news not in news_popular:
                    news_popular[news] = 0
                news_popular[news] += 1

        self.news_count = len(news_popular)
        print('新闻总个数 = %d' % self.news_count)
        # 构建新闻-用户倒排表
        print('构建新闻-用户倒排表 ...')
        new_users = dict()
        for user, news in self.trainSet.items():
            for new in news:
                if new not in new_users:
                    new_users[new] = set()
                new_users[new].add(user)
        # print(new_users)
        # 计算用户之间的相似度（采用余弦相似度）
        self.user_sim_matrix = np.zeros((len(self.trainSet), len(self.trainSet)))
        for i, u in enumerate(self.trainSet.keys()):
            for j, v in enumerate(self.trainSet.keys()):
                if i != j:
                    common_news = set(self.trainSet[u]) & set(self.trainSet[v])
                    # print(common_news)
                    if len(common_news) > 0:
                        # 计算两个用户对共同兴趣的评分向量
                        u_ratings = np.array(
                            [self.trainSet[u][new] - np.log10(1 + news_popular[new]) for new in common_news])
                        v_ratings = np.array(
                            [self.trainSet[v][new] - np.log10(1 + news_popular[new]) for new in common_news])
                        # 计算余弦相似度
                        self.user_sim_matrix[i, j] = np.dot(u_ratings, v_ratings) / (np.linalg.norm(u_ratings) * np.linalg.norm(v_ratings))
                    else:
                        self.user_sim_matrix[i, j] = 0
        # print(self.user_sim_matrix)

    # 针对目标用户U，找到其最相似的K个用户，产生N个推荐
    def recommend(self, user):
        """
            对目标用户进行商品推荐
            :param user: 目标用户ID
            :param train: 训练集，包含用户-商品评分数据
            :param sim_matrix: 相似度矩阵
            :param N: 推荐商品数量
            :return: 推荐商品列表
            """

        # 找到用户已评价过的商品集合
        news_user_evaluated = set(self.trainSet[user].keys())
        # 初始化为0，将相似度矩阵按照相似度排序后得到前N个最相似用户
        sim_ranking = np.argsort(-self.user_sim_matrix[user-1])  # 排序后的用户编号索引数组
        sim_users0 = sim_ranking[:self.n_rec_news]
        sim_users=[x+1 for x in sim_users0]   # 1-10
        # 统计每个商品被推荐的次数和总评分
        new_score = dict()
        for i in sim_users:
            # 找到与目标用户最相似的用户已评价过的商品
            news_sim_user_evaluated = set(self.trainSet[i].keys())
            # 遍历目标用户未评价过的商品，计算每个商品的推荐得分
            for new in (news_sim_user_evaluated - news_user_evaluated):
                if new not in new_score:
                    new_score[new] = [0, 0]
                # print(new_score)
                # 根据最相似用户的相似度和评分计算推荐得分
                new_score[new][0] += self.user_sim_matrix[user-1][i-1] * self.trainSet[i][new]   # user_sim_matrix[user][i]表示目标用户与其他用户的相似度*其他用户对未评价过的新闻的评分
                new_score[new][1] += self.user_sim_matrix[user-1][i-1]

        # 按照推荐得分倒序排序，返回前N个推荐商品
        new_ranking = [(k, v[0] / (v[1] + 1e-6)) for k, v in new_score.items()]
        new_ranking.sort(key=lambda x: x[1], reverse=True)
        # print(new_ranking)
        recommended_news = [x[0] for x in new_ranking[:self.n_rec_news]]

        return recommended_news

    # 产生推荐并通过准确率、召回率和覆盖率进行评估
    def evaluate(self):
        """
            计算推荐算法的准确率、召回率和覆盖率
            :param test: 测试集，包含用户-商品评分数据
            :param train: 训练集，包含用户-商品评分数据
            :param sim_matrix: 相似度矩阵
            :param N: 推荐商品数量
            :return: 准确率、召回率和覆盖率
            """
        hits = 0  # 推荐的商品在测试集中出现的次数
        rec_count = 0  # 推荐的商品总数
        test_count = 0  # 测试集中的总商品数
        item_popularity = dict()  # 商品流行度字典

        # 对每个用户进行推荐
        for user in self.trainSet:
            # 找到目标用户未评价过的商品集合
            items_user_not_evaluated = set(self.testSet[user]) - set(self.trainSet[user])
            # print(items_user_not_evaluated)
            if len(items_user_not_evaluated) == 0:
                continue

            # 对目标用户进行商品推荐
            recommended_items = self.recommend(user)

            # 统计推荐商品的数量和命中次数
            rec_count += len(recommended_items)
            hits += len(set(recommended_items) & set(items_user_not_evaluated))

            # 统计测试集中的总商品数
            test_count += len(items_user_not_evaluated)

        # 计算准确率、召回率和覆盖率
        precision = hits / (1.0 * rec_count)
        recall = hits / (1.0 * test_count)
        coverage = len(item_popularity) / (1.0 * len(self.trainSet))
        print('precisioin=%.4f\trecall=%.4f\tcoverage=%.4f' % (precision, recall, coverage))
        return precision, recall, coverage

if __name__ == '__main__':
    userCF = UserBasedCF()
    ratings = Rating.query.all()
    userCF.get_dataset(ratings)
    userCF.calc_user_sim()
    userCF.evaluate()
